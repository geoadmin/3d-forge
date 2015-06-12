AliasMatch ^/${user}/3dtest(.*)$ ${directory}/3d-testapp/$1
<Directory ${directory}/3d-testapp/>
    AllowOverride None
    Order allow,deny
    Allow from all
</Directory>

ProxyPassMatch ^/${user}/tiles/([0-9]*)/(.*)$ http://localhost:9014/tiles/$1/$2
<Proxy http://localhost:9014>
    Order deny,alloW
    Allow from all
</Proxy>

ProxyPassMatch ^/${user}/tiles/(.*)$ http://ec2-54-220-242-89.eu-west-1.compute.amazonaws.com/stk-terrain/tilesets/swisseudem/tiles/$1
<Proxy http://ec2-54-220-242-89.eu-west-1.compute.amazonaws.com>
    Order deny,allow
    Allow from all
</Proxy>

