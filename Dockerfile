FROM odoo:16

COPY ./odoo_addons /usr/lib/python3/dist-packages/odoo/addons/     

# RUN ls -al /var/www/html
# RUN chown -R www-data:www-data /var/www/html 
# RUN chmod -R 755 /var/www/html