#!/bin/bash
set -e

# Esperar a que MySQL esté listo
echo "Esperando a MySQL..."
while ! mysqladmin ping -h"atom_db" --silent 2>/dev/null; do
    sleep 2
done
echo "MySQL listo!"

# Crear config.php si no existe
if [ ! -f /var/www/html/config/config.php ]; then
    echo "Creando config.php..."
    cat > /var/www/html/config/config.php << 'CONFIGEOF'
<?php
return array (
  'all' => array (
    'propel' => array (
      'class' => 'sfPropelDatabase',
      'param' => array (
        'encoding' => 'utf8mb4',
        'persistent' => true,
        'pooling' => true,
        'dsn' => 'mysql:host=atom_db;dbname=atom;charset=utf8mb4',
        'username' => 'atom',
        'password' => 'atom_pass',
      ),
    ),
  ),
);
CONFIGEOF
fi

# Crear propel.ini si no existe
if [ ! -f /var/www/html/config/propel.ini ]; then
    echo "Creando propel.ini..."
    cat > /var/www/html/config/propel.ini << 'PROPELEOF'
propel.targetPackage       = lib.model
propel.packageObjectModel  = true
propel.project             = qubit
propel.database            = mysql
propel.database.driver     = mysql
propel.database.url        = mysql:host=atom_db;dbname=atom;charset=utf8mb4
propel.database.creole.url = ${propel.database.url}
propel.database.user       = atom
propel.database.password   = atom_pass
propel.database.encoding   = utf8mb4
propel.addGenericAccessors = true
propel.addGenericMutators  = true
propel.addTimeStamp        = true
propel.schema.validate     = false
propel.useDateTimeClass    = true
propel.defaultTimeFormat   = Y-m-d H:i:s
propel.samePhpName         = true
PROPELEOF
fi

# Crear search.yml para Elasticsearch
mkdir -p /var/www/html/apps/qubit/config
cat > /var/www/html/apps/qubit/config/search.yml << 'SEARCHEOF'
all:
  server:
    host: atom_es
    port: 9200
  index:
    name: atom
SEARCHEOF

# Limpiar caché
rm -rf /var/www/html/cache/*

# Permisos
chown -R www-data:www-data /var/www/html/config /var/www/html/cache /var/www/html/log

echo "AtoM configurado. Iniciando Apache..."
exec apache2-foreground
