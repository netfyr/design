# Inkscape package checksums

`prepare_inkscape_14.sh` verifies all ten downloads against
`inkscape-1.4.sha256` before extracting packages or running Inkscape.
The filenames, versions, library paths, and wrapper match the font build's
native setup. A failed download or checksum stops preparation.

The checksums come from Debian trixie's `main/binary-amd64/Packages.xz`,
authenticated through the signed `InRelease` dated 12 September 2026.
Verification on 12 October 2026 covered all three release signatures, the
compressed package index's SHA-256, and each selected package's `Filename`
and `SHA256` fields. All ten existing local packages matched those entries.

Sources:

- [Signed release](https://deb.debian.org/debian/dists/trixie/InRelease):
  `0584fba32e13e0ab8285fb16c27adea1ec03a73669c18702821094fd6ca86675`
- [Package index](https://deb.debian.org/debian/dists/trixie/main/binary-amd64/Packages.xz):
  `7778d3e3f303b7ddb8ce0fe7c8d57473a076c6bf2e8f241f75421d2396352498`
- [Debian archive keys](https://ftp-master.debian.org/keys.html), retrieved over
  HTTPS and checked against the published fingerprints:
  - Bookworm archive: `B8B80B5B623EAB6AD8775C45B7C5D7D6350947F8`
  - Trixie archive: `04B54C3CDCA79751B16BC6B5225629DF75B188BD`
  - Trixie stable release: `41587F7DB8C774BCCF131416762F67A0B2C39DE4`

The initial key lookup relies on Debian's HTTPS service; no preinstalled Debian
keyring was available. The preparation script uses the checked-in hashes and
does not fetch signing keys or accept changed package bytes automatically.
When changing a package, verify its checksum against signed Debian metadata
before updating the manifest. The live index changes over time; the hashes
above identify the metadata used for these package versions.
