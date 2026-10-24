"""Tipos compartidos del paquete: enumeración de enlaces de redes sociales."""

from __future__ import annotations

import re
from enum import StrEnum, auto
from functools import cached_property

# Usuario de GitHub: 1-39 caracteres, sin guiones al inicio ni al final.
_GITHUB_USER = r"[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,37}[a-zA-Z0-9])?"

_FACEBOOK = r"(?:facebook\.com|fb\.com)"

_X = r"(?:x\.com|twitter\.com)"


def _social_pattern(*routes: str) -> re.Pattern[str]:
    # Cada ruta es `host/ruta`. Esquema y `www.`/`m.` opcionales; admite
    # barra final, query y fragmento.
    body = "|".join(routes)
    return re.compile(
        rf"(?:https?://)?(?:www\.|m\.)?(?:{body})/?(?:[?#]\S*)?",
        re.IGNORECASE,
    )


class SocialLink(StrEnum):
    """Tipos de enlace de red social soportados por `valid_social_url`.

    Cada miembro es una plataforma y el nombre que esa red da al contenido:
    perfil, página, repositorio, canal, reel, short, vídeo...

    Examples:
        >>> SocialLink.GITHUB_REPO
        <SocialLink.GITHUB_REPO: 'github_repo'>
        >>> SocialLink("tiktok_video") is SocialLink.TIKTOK_VIDEO
        True
        >>> bool(SocialLink.X_PROFILE.pattern.fullmatch("https://x.com/isidro_rg"))
        True
    """

    FACEBOOK_PAGE = auto()
    FACEBOOK_PROFILE = auto()
    FACEBOOK_REEL = auto()
    GITHUB_PROFILE = auto()
    GITHUB_REPO = auto()
    INSTAGRAM_PROFILE = auto()
    INSTAGRAM_REEL = auto()
    LINKEDIN_COMPANY = auto()
    LINKEDIN_PROFILE = auto()
    TIKTOK_PROFILE = auto()
    TIKTOK_VIDEO = auto()
    X_PROFILE = auto()
    YOUTUBE_CHANNEL = auto()
    YOUTUBE_SHORT = auto()
    YOUTUBE_VIDEO = auto()

    @cached_property
    def pattern(self) -> re.Pattern[str]:
        """Expresión regular compilada que valida este tipo de enlace.

        Examples:
            >>> SocialLink.YOUTUBE_SHORT.pattern.fullmatch(
            ...     "https://youtube.com/shorts/dQw4w9WgXcQ"
            ... ) is not None
            True
            >>> SocialLink.GITHUB_PROFILE.pattern.fullmatch("https://x.com/a") is None
            True
        """
        match self:
            case SocialLink.FACEBOOK_PAGE:
                return _social_pattern(rf"{_FACEBOOK}/pages/[\w%-]+/\d+")
            case SocialLink.FACEBOOK_PROFILE:
                return _social_pattern(rf"{_FACEBOOK}/[a-zA-Z0-9.]{{5,50}}")
            case SocialLink.FACEBOOK_REEL:
                return _social_pattern(rf"{_FACEBOOK}/reel/\d+")
            case SocialLink.GITHUB_PROFILE:
                return _social_pattern(rf"github\.com/{_GITHUB_USER}")
            case SocialLink.GITHUB_REPO:
                return _social_pattern(rf"github\.com/{_GITHUB_USER}/[\w.-]+")
            case SocialLink.INSTAGRAM_PROFILE:
                return _social_pattern(r"instagram\.com/[\w.]{1,30}")
            case SocialLink.INSTAGRAM_REEL:
                return _social_pattern(r"instagram\.com/reels?/[\w-]+")
            case SocialLink.LINKEDIN_COMPANY:
                return _social_pattern(r"linkedin\.com/company/[\w%-]+")
            case SocialLink.LINKEDIN_PROFILE:
                return _social_pattern(r"linkedin\.com/in/[\w%-]{3,100}")
            case SocialLink.TIKTOK_PROFILE:
                return _social_pattern(r"tiktok\.com/@[\w.]{2,24}")
            case SocialLink.TIKTOK_VIDEO:
                return _social_pattern(r"tiktok\.com/@[\w.]{2,24}/video/\d+")
            case SocialLink.X_PROFILE:
                return _social_pattern(rf"{_X}/\w{{1,15}}")
            case SocialLink.YOUTUBE_CHANNEL:
                return _social_pattern(
                    r"youtube\.com/(?:@[\w.-]{3,30}|channel/UC[\w-]{22}|(?:c|user)/[\w.-]+)"
                )
            case SocialLink.YOUTUBE_SHORT:
                return _social_pattern(r"youtube\.com/shorts/[\w-]{11}")
            case (
                _
            ):  # YOUTUBE_VIDEO: `watch?v=ID` (con otros parámetros) o `youtu.be/ID`.
                return _social_pattern(
                    r"youtube\.com/watch\?(?:[\w=%.-]+&)*v=[\w-]{11}(?:&\S*)?",
                    r"youtu\.be/[\w-]{11}",
                )
