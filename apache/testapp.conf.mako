AliasMatch ^/${user}/3dtest(.*)$ ${directory}/3d-testapp/$1
<Directory ${directory}/3d-testapp/>
    AllowOverride None
    Order allow,deny
    Allow from all
</Directory>

RewriteRule ^/${user}/tiles/([0-7]?)/(.*)$ http://ec2-54-220-242-89.eu-west-1.compute.amazonaws.com/stk-terrain/tilesets/swisseudem/tiles/$1/$2 [L,P,QSA]

RewriteRule ^/${user}/tiles/(9|10|11|12)/(.*) http://tms3d.geo.admin.ch.s3.amazonaws.com/$1/$2 [L,P,QSA]

RewriteRule ^/${user}/tiles/(.*)$ http://ec2-54-220-242-89.eu-west-1.compute.amazonaws.com/stk-terrain/tilesets/swisseudem/tiles/$1 [P,QSA]

<Location /${user}/tiles>
  Order deny,allow
  Allow from all
</Location>
