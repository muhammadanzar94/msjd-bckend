import datetime
import re

import pandas as pd
from django.core.exceptions import ValidationError

from .models import PrayerTimetable, JummaTime

REQUIRED_TIME_COLUMNS = [
    'fajr_start', 'fajr_jamaat',
    'duhr_start', 'duhr_jamaat',
    'asr_start', 'asr_jamaat',
    'maghrib_start', 'maghrib_jamaat',
    'isha_start', 'isha_jamaat',
]
OPTIONAL_TIME_COLUMNS = ['sunrise', 'sunset', 'noon']

TIME_FORMATS = ('%H:%M:%S', '%H:%M', '%I:%M %p', '%I:%M:%S %p')
DATE_FORMATS = ('%Y-%m-%d', '%d/%m/%Y', '%d-%m-%Y')


def _is_blank(value):
    return value is None or (isinstance(value, float) and pd.isna(value)) or str(value).strip() == ''


def _parse_time(value):
    if _is_blank(value):
        return None
    if isinstance(value, datetime.time):
        return value
    if isinstance(value, (datetime.datetime, pd.Timestamp)):
        return value.time()
    text = str(value).strip()
    for fmt in TIME_FORMATS:
        try:
            return datetime.datetime.strptime(text, fmt).time()
        except ValueError:
            continue
    raise ValueError(f'Unrecognized time format: {value!r}')


def _parse_date(value):
    if isinstance(value, (datetime.datetime, pd.Timestamp)):
        return value.date()
    if isinstance(value, datetime.date):
        return value
    if _is_blank(value):
        raise ValueError('date is required')
    text = str(value).strip()
    for fmt in DATE_FORMATS:
        try:
            return datetime.datetime.strptime(text, fmt).date()
        except ValueError:
            continue
    raise ValueError(f'Unrecognized date format: {value!r}')


def _parse_jumma_times(value):
    if _is_blank(value):
        return []
    return [_parse_time(part.strip()) for part in re.split(r'[;,]', str(value)) if part.strip()]


def _read_dataframe(file):
    name = (getattr(file, 'name', '') or '').lower()
    try:
        if name.endswith('.csv'):
            return pd.read_csv(file)
        return pd.read_excel(file)
    except Exception as exc:
        raise ValueError(f'Could not read file: {exc}')


def parse_bulk_upload(file, masjid):
    """Parses an uploaded CSV/XLSX of prayer times for `masjid` and
    upserts PrayerTimetable (and, if a 'jumma' column is present,
    JummaTime) rows. Bad rows are skipped and reported rather than
    aborting the whole file, so re-uploading the same sheet just
    updates the days that changed.
    """
    df = _read_dataframe(file)
    df.columns = [str(c).strip().lower() for c in df.columns]

    missing = [c for c in ['date', *REQUIRED_TIME_COLUMNS] if c not in df.columns]
    if missing:
        raise ValueError(f"Missing required column(s): {', '.join(missing)}")

    if df.empty:
        raise ValueError('No data rows found in file.')

    has_jumma_column = 'jumma' in df.columns
    created = 0
    updated = 0
    errors = []

    for idx, row in df.iterrows():
        row_num = idx + 2  # +1 for header row, +1 for 1-indexing
        try:
            date = _parse_date(row['date'])

            field_values = {}
            for col in REQUIRED_TIME_COLUMNS:
                parsed = _parse_time(row[col])
                if parsed is None:
                    raise ValueError(f'{col} is required')
                field_values[col] = parsed
            for col in OPTIONAL_TIME_COLUMNS:
                field_values[col] = _parse_time(row[col]) if col in df.columns else None

            existing = PrayerTimetable.objects.filter(masjid=masjid, date=date).first()
            instance = existing or PrayerTimetable(masjid=masjid, date=date)
            for field, value in field_values.items():
                setattr(instance, field, value)
            instance.full_clean()
            instance.save()
            updated += 1 if existing else 0
            created += 0 if existing else 1

            if has_jumma_column:
                jumma_times = _parse_jumma_times(row['jumma'])
                JummaTime.objects.filter(masjid=masjid, date=date).delete()
                for jamaat_time in jumma_times:
                    # Sheet only carries one time per Jumma slot; khutbah_start
                    # defaults to it and can be refined later via the admin API.
                    jt = JummaTime(masjid=masjid, date=date, khutbah_start=jamaat_time, jamaat_time=jamaat_time)
                    jt.full_clean()
                    jt.save()
        except (ValueError, ValidationError) as exc:
            errors.append({'row': row_num, 'error': str(exc)})

    return {'created': created, 'updated': updated, 'errors': errors}
