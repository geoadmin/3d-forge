AliasMatch ^/${user}/3dtest(.*)$ ${directory}/3d-testapp/$1
<Directory ${directory}/3d-testapp/>
    AllowOverride None
    Order allow,deny
    Allow from all
</Directory>
