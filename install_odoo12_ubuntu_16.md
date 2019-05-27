Instrucciones para odoo12 y ubuntu 16:
---
apt-get update && apt upgrade
apt-get install python3-pip
pip3 install --upgrade pip
apt-get install postgresql
systemctl start postgresql
systemctl enable postgresql
wget -O - https://nightly.odoo.com/odoo.key | apt-key add -
echo "deb http://nightly.odoo.com/12.0/nightly/deb/ ./" >> /etc/apt/sources.list.d/odoo.list
apt-get update
apt-get install odoo
systemctl status odoo

sudo wget https://github.com/wkhtmltopdf/wkhtmltopdf/releases/download/0.12.1/wkhtmltox-0.12.1_linux-trusty-amd64.deb
dpkg -i wkhtmltox-0.12.1_linux-trusty-amd64.deb 

apt-get install -y node-less
apt-get install -y npm
ln -s /usr/bin/nodejs /usr/bin/node
npm install -g less less-plugin-clean-css
apt-get install tesseract-ocr-eng
pip3.5 install --upgrade pip
pip3.5 install pytesseract
--si presenta error en pip3
--python3 -m pip uninstall pip && sudo apt install python3-pip --reinstall
--pip3 install --upgrade pip
apt-get install git
apt-get install xmlsec1
apt-get install libxmlsec1-dev 
apt-get install python3-pysimplesoap
pip3.5 install pdf417gen
pip3.5 install python-barcode
pip3.5 install xmlsec
systemctl restart odoo

Posibles errores / correccion:
File "/usr/local/lib/python3.5/dist-packages/pip/_vendor/urllib3/contrib/pyopenssl.py", line 46, in <module>
    import OpenSSL.SSL
  File "/usr/lib/python3/dist-packages/OpenSSL/__init__.py", line 8, in <module>
    from OpenSSL import rand, crypto, SSL
  File "/usr/lib/python3/dist-packages/OpenSSL/SSL.py", line 118, in <module>
    SSL_ST_INIT = _lib.SSL_ST_INIT
-----
rm -rf /usr/lib/python3/dist-packages/OpenSSL/
rm -rf /usr/lib/python3/dist-packages/pyOpenSSL-0.15.1.egg-info/
pip3.5 install  pyopenssl
-----------
python3 -m pip install --upgrade pip==9.0.3
------------------
pip3.5 install --upgrade cryptography
pip3.5 install --upgrade xmlsec
