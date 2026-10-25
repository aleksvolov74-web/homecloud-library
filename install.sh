#!/usr/bin/env bash
set -Eeuo pipefail

APP="/srv/clouddata/library/flibusta-app/app"
REPO="https://raw.githubusercontent.com/aleksvolov74-web/homecloud-library/main"
BACKUP="$APP/server.py.backup-$(date +%Y%m%d-%H%M%S)"
TMP="$(mktemp)"

rollback() {
    echo "Ошибка! Восстанавливаю предыдущую версию."
    if [[ -f "$BACKUP" ]]; then
        cp "$BACKUP" "$APP/server.py"
        sudo systemctl restart flibusta.service
    fi
    rm -f "$TMP"
}

trap rollback ERR

echo "=== Загрузка обновления ==="
curl -fLsS "$REPO/server.py" -o "$TMP"

echo "=== Проверка синтаксиса ==="
python3 -m py_compile "$TMP"

echo "=== Резервная копия ==="
cp -a "$APP/server.py" "$BACKUP"

echo "=== Установка ==="
cp "$TMP" "$APP/server.py"
sudo systemctl restart flibusta.service

echo "=== Проверка сайта ==="
sleep 3
curl -fLsS -o /dev/null "http://192.168.1.198:8090/"
curl -fLsS -o /dev/null "http://192.168.1.198:8090/?q=Пушкин"

trap - ERR
rm -f "$TMP"

echo "=== ОБНОВЛЕНИЕ УСТАНОВЛЕНО ==="
