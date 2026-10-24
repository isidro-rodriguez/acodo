"""Tests de las validaciones (`valid_*`)."""

import pytest

import acodo.utils as iu
from acodo.utils.types import SocialLink


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("Sí", True),
        (" OFF ", True),
        ("1", True),
        ("verdadero", True),
        ("quizás", False),
        ("2", False),
        ("", False),
    ],
)
def test_valid_bool(raw: str, expected: bool) -> None:
    assert iu.valid_bool(raw) is expected


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("ESPCESMMXXX", True),
        ("espcesmmxxx", True),
        ("ESPCESMM", True),
        ("ESPCESMM123", True),
        ("ESPCESMMX", False),
        ("ESPCES", False),
        ("1234ESMMXXX", False),
        ("", False),
    ],
)
def test_valid_bic(raw: str, expected: bool) -> None:
    assert iu.valid_bic(raw) is expected


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("31/01/2024", True),
        ("2024-01-31", True),
        (" 2024-01-31 ", True),
        ("basura", False),
        ("31/02/2024", False),
        ("", False),
    ],
)
def test_valid_date(raw: str, expected: bool) -> None:
    assert iu.valid_date(raw) is expected


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("2024-01-31", True),
        (" 2024-01-31 ", True),
        ("31/01/2024", True),
        ("1700000000", True),
        ("basura", False),
        ("31/02/2024", False),
        ("", False),
    ],
)
def test_valid_datetime(raw: str, expected: bool) -> None:
    assert iu.valid_datetime(raw) is expected


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("12345678Z", True),
        ("12345678z", True),
        ("00000000T", True),
        ("12345678A", False),
        ("1234567Z", False),
        ("ABCDEFGHZ", False),
        ("", False),
    ],
)
def test_valid_dni(raw: str, expected: bool) -> None:
    assert iu.valid_dni(raw) is expected


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("example.com", True),
        ("sub.dominio.example.com", True),
        ("EXAMPLE.COM", True),
        ("a" * 63 + ".com", True),
        ("example", False),
        ("example.c", False),
        ("example.123", False),
        ("-example.com", False),
        ("example-.com", False),
        ("exa mple.com", False),
        ("example.com.", False),
        ("a" * 64 + ".com", False),
        ("example..com", False),
        (".com", False),
        ("", False),
    ],
)
def test_valid_domain(raw: str, expected: bool) -> None:
    assert iu.valid_domain(raw) is expected


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("1h 30m", True),
        ("2d", True),
        ("1,5h", True),
        ("1h30x", False),
        ("basura", False),
        ("", False),
    ],
)
def test_valid_duration(raw: str, expected: bool) -> None:
    assert iu.valid_duration(raw) is expected


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("a@b.com", True),
        ("user.name+tag@example.co.uk", True),
        ("hola", False),
        ("a@b", False),
        ("@b.com", False),
        ("a b@c.com", False),
        ("a@b.com basura", False),
        ("a@b.com\n", False),
        ("a..b@c.com", False),
        (".a@c.com", False),
        ("a.@c.com", False),
        ("a.b@c.com", True),
        ("x" * 250 + "@b.com", False),
        ("", False),
    ],
)
def test_valid_email(raw: str, expected: bool) -> None:
    assert iu.valid_email(raw) is expected


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("informe.pdf", True),
        ("a b.txt", True),
        (".gitignore", True),
        ("console.txt", True),
        ("a" * 255, True),
        ("", False),
        ("a" * 256, False),
        ("a/b", False),
        ("a\\b", False),
        ("a:b", False),
        ("a\x00b", False),
        ("a\tb", False),
        ("archivo.", False),
        ("archivo ", False),
        ("..", False),
        ("CON", False),
        ("con.txt", False),
        ("COM1.tar.gz", False),
        ("lpt9", False),
        ("con .txt", False),
    ],
)
def test_valid_filename(raw: str, expected: bool) -> None:
    assert iu.valid_filename(raw) is expected


@pytest.mark.parametrize(
    ("raw", "allow_alpha", "expected"),
    [
        ("#fff", True, True),
        ("#FFFF", True, True),
        ("#ff00cc", True, True),
        ("#ff00cc80", True, True),
        ("#fff", False, True),
        ("#ff00cc", False, True),
        ("#ffff", False, False),
        ("#ff00cc80", False, False),
        ("fff", True, False),
        ("#ggg", True, False),
        ("#12345", True, False),
        ("", True, False),
    ],
)
def test_valid_hex_color(raw: str, allow_alpha: bool, expected: bool) -> None:
    assert iu.valid_hex_color(raw, allow_alpha) is expected


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("ES91 2100 0418 4502 0005 1332", True),
        ("es9121000418450200051332", True),
        ("GB82 WEST 1234 5698 7654 32", True),
        ("DE89 3704 0044 0532 0130 00", True),
        ("ES91 2100 0418 4502 0005 1333", False),
        ("ES9", False),
        ("1234 5678 9012 3456", False),
        ("ES91-2100", False),
        ("", False),
    ],
)
def test_valid_iban(raw: str, expected: bool) -> None:
    assert iu.valid_iban(raw) is expected


@pytest.mark.parametrize(
    ("raw", "version", "expected"),
    [
        ("192.168.1.1", None, True),
        ("::1", None, True),
        ("1.2.3.4", 4, True),
        ("::1", 6, True),
        ("::1", 4, False),
        ("1.2.3.4", 6, False),
        ("999.1.1.1", None, False),
        ("1.2.3.4 ", None, False),
        ("", None, False),
    ],
)
def test_valid_ip(raw: str, version: int | None, expected: bool) -> None:
    assert iu.valid_ip(raw, version) is expected


def test_valid_ip_invalid_version() -> None:
    with pytest.raises(ValueError, match="version"):
        iu.valid_ip("1.2.3.4", 5)


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ('{"a": [1, 2]}', True),
        ("123", True),
        ("null", True),
        ("{'a': 1}", False),
        ("NaN", False),
        ("Infinity", False),
        ("-Infinity", False),
        ("[1,", False),
        ("", False),
        ("[" * 100_000, False),
    ],
    ids=[
        "object",
        "number",
        "null",
        "single-quotes",
        "nan",
        "infinity",
        "neg-infinity",
        "truncated-array",
        "empty",
        "deep-nesting-100k",
    ],
)
def test_valid_json(raw: str, expected: bool) -> None:
    assert iu.valid_json(raw) is expected


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("00:1A:2B:3C:4D:5E", True),
        ("00-1a-2b-3c-4d-5e", True),
        ("001A.2B3C.4D5E", True),
        ("001a2b3c4d5e", True),
        ("00:1A-2B:3C-4D:5E", False),
        ("00:1A:2B:3C:4D", False),
        ("GG:1A:2B:3C:4D:5E", False),
        ("00:1A:2B:3C:4D:5E:6F", False),
        ("", False),
    ],
)
def test_valid_mac(raw: str, expected: bool) -> None:
    assert iu.valid_mac(raw) is expected


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("X1234567L", True),
        ("x1234567l", True),
        ("Y1234567X", True),
        ("Z1234567R", True),
        ("X1234567A", False),
        ("A1234567L", False),
        ("12345678Z", False),
        ("", False),
    ],
)
def test_valid_nie(raw: str, expected: bool) -> None:
    assert iu.valid_nie(raw) is expected


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("ABC123456", True),
        ("abc123456", True),
        ("12345678", True),
        ("AB123", False),
        ("ABC-1234", False),
        ("ABCDEFGHIJK", False),
        ("ABC 12345", False),
        ("", False),
    ],
)
def test_valid_passport(raw: str, expected: bool) -> None:
    assert iu.valid_passport(raw) is expected


class TestValidPassword:
    @pytest.mark.parametrize(
        ("raw", "kwargs", "expected"),
        [
            ("abc123", {}, True),
            ("Abc123", {}, True),
            ("Abc123", {"allow_uppercase": False}, False),
            ("abc#1", {"special_characters": "#"}, True),
            ("abc#1", {}, False),
            ("añb1", {}, True),
            ("abc", {}, False),
            ("a" * 11, {}, False),
            ("1234", {"only_digits": True}, True),
            ("12a4", {"only_digits": True}, False),
        ],
    )
    def test_validation(
        self, raw: str, kwargs: dict[str, object], expected: bool
    ) -> None:
        assert iu.valid_password(raw, (4, 10), **kwargs) is expected  # ty: ignore[invalid-argument-type]

    def test_ambiguous_arguments(self) -> None:
        with pytest.raises(ValueError, match="ambiguos"):
            iu.valid_password("1234", (4, 10), special_characters="#", only_digits=True)

    def test_inconsistent_length(self) -> None:
        with pytest.raises(ValueError, match="incoherente"):
            iu.valid_password("abcd", (10, 4))


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("+34 612 345 678", True),
        (" +34612345678 ", True),
        ("(91) 123-4567", True),
        ("612.345.678", True),
        ("12345", False),
        ("+34 612 345 678 901 234", False),
        ("+(34", False),
        ("612 345 67a", False),
        ("abc", False),
        ("", False),
    ],
)
def test_valid_phone(raw: str, expected: bool) -> None:
    assert iu.valid_phone(raw) is expected


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("80", True),
        ("8080", True),
        ("65535", True),
        ("0", False),
        ("65536", False),
        ("-1", False),
        ("3.5", False),
        ("abc", False),
        ("", False),
    ],
)
def test_valid_port(raw: str, expected: bool) -> None:
    assert iu.valid_port(raw) is expected


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("hola-mundo", True),
        ("a", True),
        ("a1-b2", True),
        ("Hola Mundo", False),
        ("hola--mundo", False),
        ("-hola", False),
        ("hola-", False),
        ("", False),
    ],
)
def test_valid_slug(raw: str, expected: bool) -> None:
    assert iu.valid_slug(raw) is expected


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("https://example.com/x", True),
        ("http://localhost:8000", True),
        ("HTTP://EXAMPLE.COM", True),
        ("ftp://example.com", False),
        ("example.com", False),
        ("http://", False),
        ("http://@", False),
        ("http://exa mple.com", False),
        ("http://[::1", False),
        ("http://a:99999999", False),
        ("", False),
    ],
)
def test_valid_url(raw: str, expected: bool) -> None:
    assert iu.valid_url(raw) is expected


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("123e4567-e89b-12d3-a456-426614174000", True),
        ("123E4567-E89B-12D3-A456-426614174000", True),
        ("123e4567", False),
        ("123e4567e89b12d3a456426614174000", False),
        ("123e4567-e89b-12d3-a456-42661417400g", False),
        ("", False),
    ],
)
def test_valid_uuid(raw: str, expected: bool) -> None:
    assert iu.valid_uuid(raw) is expected


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("A58818501", True),
        ("B12345674", True),
        ("a58818501", True),
        ("A58818502", False),
        ("B1234567D", False),  # B exige dígito de control.
        ("Q2826000H", True),  # Q exige letra de control.
        ("P2800000H", True),
        ("P28000008", False),
        ("C0000000" + "0", True),  # C admite dígito...
        ("C0000000" + "J", True),  # ...o letra.
        ("C0000000" + "A", False),
        ("I12345674", False),  # Letra de entidad no válida.
        ("B123456", False),
        ("", False),
    ],
)
def test_valid_cif(raw: str, expected: bool) -> None:
    assert iu.valid_cif(raw) is expected


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("12345678Z", True),
        ("X1234567L", True),
        ("K1234567L", True),
        ("m1234567l", True),
        ("12345678A", False),
        ("X1234567A", False),
        ("K1234567A", False),
        ("A58818501", False),
        ("", False),
    ],
)
def test_valid_nif(raw: str, expected: bool) -> None:
    assert iu.valid_nif(raw) is expected


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("38001", True),
        ("35500", True),
        ("01001", True),
        ("52999", True),
        ("00001", False),
        ("53000", False),
        ("3800", False),
        ("380011", False),
        ("3800a", False),
        ("٣٨٠٠١", False),  # Dígitos no ASCII.
        ("", False),
    ],
)
def test_valid_postal_code(raw: str, expected: bool) -> None:
    assert iu.valid_postal_code(raw) is expected


@pytest.mark.parametrize(
    ("raw", "link", "expected"),
    [
        ("https://github.com/isidro-rodriguez", "GITHUB_PROFILE", True),
        ("github.com/isidro-rodriguez/acodo-utils", "GITHUB_REPO", True),
        ("https://github.com/-malo", "GITHUB_PROFILE", False),
        ("https://github.com/user", "GITHUB_REPO", False),
        ("https://facebook.com/isidro.rodriguez", "FACEBOOK_PROFILE", True),
        ("https://m.facebook.com/pages/Mi-Pagina/123456", "FACEBOOK_PAGE", True),
        ("https://fb.com/reel/123456789", "FACEBOOK_REEL", True),
        ("https://x.com/isidro_rg", "X_PROFILE", True),
        ("http://twitter.com/isidro_rg/", "X_PROFILE", True),
        ("https://x.com/nombre_demasiado_largo", "X_PROFILE", False),
        ("https://instagram.com/isidro.rg?hl=es", "INSTAGRAM_PROFILE", True),
        ("https://www.instagram.com/reel/C1a2B3c/", "INSTAGRAM_REEL", True),
        ("https://www.tiktok.com/@isidro", "TIKTOK_PROFILE", True),
        ("https://www.tiktok.com/@isidro/video/123", "TIKTOK_VIDEO", True),
        ("https://tiktok.com/isidro", "TIKTOK_PROFILE", False),
        ("https://linkedin.com/in/isidro-rodriguez", "LINKEDIN_PROFILE", True),
        ("https://linkedin.com/company/acme", "LINKEDIN_COMPANY", True),
        ("https://www.youtube.com/@isidro", "YOUTUBE_CHANNEL", True),
        (
            "https://youtube.com/channel/UCabcdefghijklmnopqrstuv",
            "YOUTUBE_CHANNEL",
            True,
        ),
        ("https://youtube.com/c/isidro", "YOUTUBE_CHANNEL", True),
        ("https://youtube.com/user/isidro", "YOUTUBE_CHANNEL", True),
        ("https://youtube.com/shorts/dQw4w9WgXcQ", "YOUTUBE_SHORT", True),
        ("https://www.youtube.com/watch?v=dQw4w9WgXcQ", "YOUTUBE_VIDEO", True),
        (
            "https://youtube.com/watch?list=PL1&v=dQw4w9WgXcQ&t=10",
            "YOUTUBE_VIDEO",
            True,
        ),
        ("https://youtu.be/dQw4w9WgXcQ?t=10", "YOUTUBE_VIDEO", True),
        ("https://youtu.be/corto", "YOUTUBE_VIDEO", False),
        ("  https://github.com/isidro-rodriguez  ", "GITHUB_PROFILE", True),
        ("ftp://github.com/isidro-rodriguez", "GITHUB_PROFILE", False),
        ("https://github.com.evil.com/user", "GITHUB_PROFILE", False),
        ("https://x.com/user", "GITHUB_PROFILE", False),
        ("", "GITHUB_PROFILE", False),
    ],
)
def test_valid_social_url(raw: str, link: str, expected: bool) -> None:
    assert iu.valid_social_url(raw, SocialLink[link]) is expected
