# Bad Cloud

# Requirements

- python3 (/usr/bin/python3)
- webserver
- node / npm
- git

# Installation

```bash
# clone the repo
git clone git@github.com:b4dr1ck/BadCloud.git
# cd to the project folder
cd BadCloud
# install node modules
npm i
# build the project
npm run build
# cd to the dist/ folder (the builded project)
cd dist/
# deploy to your webserver
cp -r * /var/www/html # path to you webserver DOCROOT
cp src/fileRequest.py /var/www/html # path to you webserver DOCROOT
```

# Config File

create a config file in your **$HOME** named **.badCloud.json**
If you want to change the path or filename of the config-file you have to do it in the backend sript **src/fileRequest.py**

```python
configFile = os.path.join(os.environ.get("HOME"), ".badCloud.json")
```

```json
{
  "UPLOAD_DIR": "/home/itsv.org.sv-services.at/patrick.reiter@itsv.at/uploads",
  "MAX_FILE_SIZE": 10485760,
  "MAX_TOTAL_SIZE": 104857600,
  "ALLOWED_FILETYPE": [
    "image/png",
    "image/jpeg",
    "image/jpg",
    "image/gif",
    "application/pdf",
    "application/zip",
    "application/json",
    "text/plain",
    "text/csv",
    "text/html",
    "text/markdown"
  ]
}
```

- UPLOAD_DIR
  - Target for Files to Upload
- MAX_FILE_SIZE
  - maximal file size for files to upload in bytes
- MAX_TOTAL_SIZE
  - maximal available space in your UPLOAD_DIR
- ALLOWED_FILETYPE
  - allowed mime-types for to upload

# Base Url

to change the base directory of the project on your webserver (default is /), you have to change the vite.config.js

```js
export default defineConfig({
  base: "/", // change this value
  plugins: [vue(), vueDevTools()],
  resolve: {
    alias: {
      "@": fileURLToPath(new URL("./src", import.meta.url)),
    },
  },
});
```
