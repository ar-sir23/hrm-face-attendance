#!/bin/bash
BACKUP_DIR="/home/md-abdur-rahman/hrm_backups"
DATE=$(date +%Y%m%d_%H%M%S)
mkdir -p $BACKUP_DIR
PGPASSWORD=Hrm2024 pg_dump -h localhost -U hrm_user hrm_attendance \
    > "$BACKUP_DIR/db_$DATE.sql"
tar -czf "$BACKUP_DIR/faces_$DATE.tar.gz" \
    /home/md-abdur-rahman/hrm_face_attendance/backend/face_images/ 2>/dev/null
cd $BACKUP_DIR
ls -t db_*.sql    | tail -n +31 | xargs rm -f 2>/dev/null
ls -t faces_*.tar.gz | tail -n +31 | xargs rm -f 2>/dev/null
echo "✅ Backup done: $DATE"
