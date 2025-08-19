#!/bin/sh
set -e
ENV_FILE=${1:-.env}
TMP_FILE="${ENV_FILE}.tmp"

awk '
# Convert leading ; to # for comments
/^;/ { sub(/^;/,"#"); print; next }
# Skip duplicate OIC_INSTANCE_NAME lines after first
/^OIC_INSTANCE_NAME=/ {
  if (seen_instance==1) next; seen_instance=1
}
# Stitch multi-line OAUTH_SCOPE (two-line pattern)
BEGIN { holding=0; scope="" }
{
  if (holding==1) {
    scope = scope $0
    printf("OAUTH_SCOPE=\"%s\"\n", scope)
    holding=0; scope=""
    next
  }
  if ($0 ~ /^OAUTH_SCOPE=/ && $0 !~ /\"/ && $0 !~ /resource:consumer::all$/) {
    sub(/^OAUTH_SCOPE=/, "", $0); scope=$0; holding=1; next
  }
  print
}
END {
  if (holding==1) {
    printf("OAUTH_SCOPE=\"%s\"\n", scope)
  }
}
' "$ENV_FILE" > "$TMP_FILE"

mv "$TMP_FILE" "$ENV_FILE"
echo "Sanitized $ENV_FILE" 