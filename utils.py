# utils.py

nama_hari = {
    "Monday": "Senin",
    "Tuesday": "Selasa",
    "Wednesday": "Rabu",
    "Thursday": "Kamis",
    "Friday": "Jumat",
    "Saturday": "Sabtu",
    "Sunday": "Minggu"
}

nama_bulan = {
    "January": "Januari",
    "February": "Februari",
    "March": "Maret",
    "April": "April",
    "May": "Mei",
    "June": "Juni",
    "July": "Juli",
    "August": "Agustus",
    "September": "September",
    "October": "Oktober",
    "November": "November",
    "December": "Desember"
}

def format_datetime_indo(dt):
    hari = nama_hari[dt.strftime('%A')]
    tanggal = dt.strftime('%d')
    bulan = nama_bulan[dt.strftime('%B')]
    tahun = dt.strftime('%Y')
    jam = dt.strftime('%H:%M')
    return f"{hari}, {tanggal} {bulan} {tahun} • {jam}"
