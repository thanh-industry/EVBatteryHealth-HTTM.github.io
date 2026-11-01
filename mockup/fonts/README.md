# Fonts

These files are bundled so the mockup renders identically with no network
connection. Nothing here is loaded from a CDN.

| Family | Files | Use |
|---|---|---|
| Inter | `inter-{400,500,600,700}.woff2` (Latin) and `inter-vi-{400,500,600,700}.woff2` (Vietnamese) | All UI text |
| JetBrains Mono | `jbmono-{400,600}.woff2` | Serial numbers, metrics, timestamps |

The Latin and Vietnamese files are separate subsets selected by `unicode-range`
in `../css/tokens.css`: a browser downloads the Vietnamese subset only when a
page actually renders Vietnamese characters, which keeps the common case small
while guaranteeing the diacritics in "Phạm Văn Thành", "Đồng Quang Trí" and
"Quản Thành Thơ" always render correctly.

Total payload: roughly 180 KB.

## Licence

Both families are licensed under the SIL Open Font License 1.1, which permits
redistribution of the font files alongside this project.

- Inter - Rasmus Andersson - https://github.com/rsms/inter
- JetBrains Mono - JetBrains - https://github.com/JetBrains/JetBrainsMono

Full licence text: https://openfontlicense.org
