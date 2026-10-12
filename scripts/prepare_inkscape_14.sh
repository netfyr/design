#!/usr/bin/env bash
set -euo pipefail
cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.."
mkdir -p .build/native/inkscape-1.4-libs .build/native/inkscape-1.4 .build/native/bin-1.4
curl -fsSL https://deb.debian.org/debian/pool/main/i/inkscape/inkscape_1.4-6_amd64.deb -o .build/native/inkscape-1.4.deb
curl -fsSL https://deb.debian.org/debian/pool/main/b/boost1.83/libboost-filesystem1.83.0_1.83.0-4.2_amd64.deb -o .build/native/boost-1.83.deb
curl -fsSL https://deb.debian.org/debian/pool/main/p/poppler/libpoppler147_25.03.0-5+deb13u4_amd64.deb -o .build/native/poppler-147.deb
curl -fsSL https://deb.debian.org/debian/pool/main/libj/libjpeg-turbo/libjpeg62-turbo_2.1.5-4_amd64.deb -o .build/native/jpeg-62.deb
curl -fsSL https://deb.debian.org/debian/pool/main/c/curl/libcurl3t64-gnutls_8.14.1-2+deb13u5_amd64.deb -o .build/native/curl-gnutls.deb
curl -fsSL https://deb.debian.org/debian/pool/main/g/gpgme1.0/libgpgmepp6t64_1.24.2-3_amd64.deb -o .build/native/gpgmepp-6.deb
curl -fsSL https://deb.debian.org/debian/pool/main/g/gpgme1.0/libgpgme11t64_1.24.2-3_amd64.deb -o .build/native/gpgme-11.deb
curl -fsSL https://deb.debian.org/debian/pool/main/r/rtmpdump/librtmp1_2.4+20151223.gitfa8646d.1-2+b5_amd64.deb -o .build/native/rtmp-1.deb
curl -fsSL https://deb.debian.org/debian/pool/main/liba/libassuan/libassuan9_3.0.2-2_amd64.deb -o .build/native/assuan-9.deb
curl -fsSL https://deb.debian.org/debian/pool/main/p/poppler/libpoppler-glib8t64_25.03.0-5+deb13u4_amd64.deb -o .build/native/poppler-glib-8.deb
(cd .build/native && sha256sum --strict --check ../../scripts/inkscape-1.4.sha256)
bsdtar -xOf .build/native/inkscape-1.4.deb data.tar.xz | bsdtar -xf - -C .build/native/inkscape-1.4
bsdtar -xOf .build/native/boost-1.83.deb data.tar.xz | bsdtar -xf - -C .build/native/inkscape-1.4-libs
bsdtar -xOf .build/native/poppler-147.deb data.tar.xz | bsdtar -xf - -C .build/native/inkscape-1.4-libs
bsdtar -xOf .build/native/jpeg-62.deb data.tar.xz | bsdtar -xf - -C .build/native/inkscape-1.4-libs
bsdtar -xOf .build/native/curl-gnutls.deb data.tar.xz | bsdtar -xf - -C .build/native/inkscape-1.4-libs
bsdtar -xOf .build/native/gpgmepp-6.deb data.tar.xz | bsdtar -xf - -C .build/native/inkscape-1.4-libs
bsdtar -xOf .build/native/gpgme-11.deb data.tar.xz | bsdtar -xf - -C .build/native/inkscape-1.4-libs
bsdtar -xOf .build/native/rtmp-1.deb data.tar.xz | bsdtar -xf - -C .build/native/inkscape-1.4-libs
bsdtar -xOf .build/native/assuan-9.deb data.tar.xz | bsdtar -xf - -C .build/native/inkscape-1.4-libs
bsdtar -xOf .build/native/poppler-glib-8.deb data.tar.xz | bsdtar -xf - -C .build/native/inkscape-1.4-libs
LD_LIBRARY_PATH="$PWD/.build/native/inkscape-1.4-libs/usr/lib/x86_64-linux-gnu" ldd -v .build/native/inkscape-1.4/usr/bin/inkscape > .build/native/inkscape-1.4-linker-report.txt 2>&1
if rg 'not found' .build/native/inkscape-1.4-linker-report.txt; then
  exit 1
fi
LD_LIBRARY_PATH="$PWD/.build/native/inkscape-1.4-libs/usr/lib/x86_64-linux-gnu" .build/native/inkscape-1.4/usr/bin/inkscape --version
cat > .build/native/bin-1.4/inkscape <<'WRAPPER'
#!/usr/bin/env bash
set -euo pipefail
native_root="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
export LD_LIBRARY_PATH="$native_root/inkscape-1.4-libs/usr/lib/x86_64-linux-gnu"
exec dbus-run-session -- "$native_root/inkscape-1.4/usr/bin/inkscape" "$@"
WRAPPER
chmod +x .build/native/bin-1.4/inkscape
