#!/usr/bin/env bash
# Re-run the footprinting lab. Pass a domain you own or are authorised to test.
#
#   bash tools/run_recon.sh example.com
#
# Any target other than the IANA documentation domain requires CONFIRM=yes,
# so this script cannot be pointed at someone else's site by accident.
set -uo pipefail

TARGET="${1:-example.com}"
RAW="$(cd "$(dirname "$0")/.." && pwd)/recon/raw"

if [[ "$TARGET" != "example.com" && "${CONFIRM:-no}" != "yes" ]]; then
  echo "refusing: '$TARGET' is not the documentation domain."
  echo "         re-run with CONFIRM=yes only if you own it or have written permission."
  exit 1
fi

for t in whois whatweb nslookup curl wafw00f dnsrecon dig; do
  command -v "$t" >/dev/null || { echo "missing tool: $t (apt install $t)"; exit 1; }
done

mkdir -p "$RAW"
cd "$RAW" || exit 1
echo "target: $TARGET   host: $(uname -srm)   started: $(date -u +%FT%TZ)" > 00-meta.txt

whois "$TARGET"                    > 01-whois.txt      2>&1
nslookup "$TARGET"                 > 02-nslookup.txt   2>&1
dig "$TARGET" +noall +answer       > 03-dig.txt        2>&1
curl -sS -D - -o /dev/null -m 20 "https://$TARGET" > 04-curl-headers.txt 2>&1
whatweb -a 1 "https://$TARGET"     > 05-whatweb.txt    2>&1
wafw00f "https://$TARGET"          > 06-wafw00f.txt    2>&1
timeout 120 dnsrecon -d "$TARGET" -t std > 07-dnsrecon.txt 2>&1

echo "finished: $(date -u +%FT%TZ)" >> 00-meta.txt
echo "wrote $(ls -1 *.txt | wc -l) files to $RAW"
wc -l ./*.txt
