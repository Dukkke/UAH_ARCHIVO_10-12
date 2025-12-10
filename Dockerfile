FROM php:7.4-apache-bullseye

# Instalar dependencias del sistema
RUN apt-get update && apt-get install -y \
    git unzip wget curl gnupg2 \
    libicu-dev g++ libpng-dev libjpeg-dev libfreetype6-dev \
    libxslt1-dev zlib1g-dev libzip-dev \
    imagemagick ghostscript poppler-utils openjdk-11-jre-headless \
    build-essential autoconf pkg-config re2c \
    default-mysql-client \
    && rm -rf /var/lib/apt/lists/*

# --- Extensiones PHP ---
RUN docker-php-ext-install intl
RUN docker-php-ext-install pdo pdo_mysql
RUN docker-php-ext-configure gd --with-freetype --with-jpeg \
    && docker-php-ext-install gd
RUN docker-php-ext-install xsl
RUN docker-php-ext-install zip
RUN docker-php-ext-install opcache

# APCu
RUN pecl install apcu \
    && docker-php-ext-enable apcu

# --- Composer ---
RUN curl -sS https://getcomposer.org/installer | php \
    -- --install-dir=/usr/local/bin --filename=composer

# Configuración de PHP
RUN echo "[PHP]" > /usr/local/etc/php/conf.d/atom.ini && \
    echo "memory_limit=1024M" >> /usr/local/etc/php/conf.d/atom.ini && \
    echo "error_reporting = E_ALL & ~E_DEPRECATED & ~E_STRICT & ~E_NOTICE" >> /usr/local/etc/php/conf.d/atom.ini && \
    echo "display_errors = Off" >> /usr/local/etc/php/conf.d/atom.ini && \
    echo "display_startup_errors = Off" >> /usr/local/etc/php/conf.d/atom.ini && \
    echo "log_errors = On" >> /usr/local/etc/php/conf.d/atom.ini && \
    echo "error_log = /var/log/php_errors.log" >> /usr/local/etc/php/conf.d/atom.ini

# --- Descargar AtoM 2.8 (más compatible con PHP 7.4) ---
RUN git clone -b stable/2.8.x --depth 1 https://github.com/artefactual/atom.git /var/www/html

WORKDIR /var/www/html

# Instalar dependencias con Composer
RUN COMPOSER_ALLOW_SUPERUSER=1 composer install --no-dev --optimize-autoloader

# Copiar vendor/symfony con Symfony 1.4 correcto
RUN if [ -d "/var/www/html/symfony1-1.4.20" ]; then \
    rm -rf /var/www/html/vendor/symfony 2>/dev/null; \
    cp -r /var/www/html/symfony1-1.4.20 /var/www/html/vendor/symfony; \
    fi

# Permisos
RUN chown -R www-data:www-data /var/www/html
RUN mkdir -p /var/www/html/cache /var/www/html/log /var/www/html/uploads
RUN chown -R www-data:www-data /var/www/html/cache /var/www/html/log /var/www/html/uploads
RUN chmod -R 775 /var/www/html/cache /var/www/html/log /var/www/html/uploads

# Activar mod_rewrite
RUN a2enmod rewrite

# Configurar Apache para permitir .htaccess
RUN sed -i '/<Directory \/var\/www\/>/,/<\/Directory>/ s/AllowOverride None/AllowOverride All/' /etc/apache2/apache2.conf

# Log de errores PHP
RUN touch /var/log/php_errors.log && chmod 666 /var/log/php_errors.log

# Copiar script de entrada
COPY docker/entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

EXPOSE 80
CMD ["/entrypoint.sh"]
