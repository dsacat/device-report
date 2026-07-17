from device_report.models import Diagnostic, Field, ReportData, Section, Table


def test_section_omits_empty_fields_but_keeps_zero_and_false():
    fields = [
        Field("name", "Ryzen"),
        Field("empty", ""),
        Field("missing", None),
        Field("items", []),
        Field("zero", 0),
        Field("disabled", False),
    ]

    section = Section(key="cpu", title="CPU", fields=fields)

    assert section.nonempty_fields() == [
        Field("name", "Ryzen"),
        Field("zero", 0),
        Field("disabled", False),
    ]


def test_report_data_is_composed_from_typed_sections_and_diagnostics():
    table = Table(headers=("Name", "Version"), rows=(("Driver", "1.0"),))
    section = Section(key="drivers", title="Drivers", tables=[table])
    diagnostic = Diagnostic(source="audio", message="Unavailable")

    report = ReportData(
        language="en",
        title="Desktop PC",
        generated_at="2026-07-17 18:30:00",
        sections=[section],
        diagnostics=[diagnostic],
    )

    assert report.sections[0].tables[0].rows == (("Driver", "1.0"),)
    assert report.diagnostics == [diagnostic]
