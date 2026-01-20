<script>
import { VFileUpload, VFileUploadItem } from "vuetify/labs/VFileUpload";

export default {
  name: "App",
  data() {
    return {
      currentDirectory: [],
      compact: false,
      checkedFiles: [],
      typeIcons: {
        image: "mdi-file-image",
        text: "mdi-file-document",
        application: "mdi-application-cog",
        unknown: "mdi-file-question",
      },
      dialog: false,
      log: "",
      errorTitle: "",
      errorMsg: "",
      snackbar: false,
      loading: true,
      url: "http://127.0.0.1/fileRequest.py",
      fileList: [],
      search: "",
      sortBy: [{ key: "filename", order: "asc" }],
      fileListHeaders: [
        {
          key: "filename",
          title: "Filename",
        },
        { key: "size", title: "Size (KB)" },
        { key: "created", title: "Created" },
        { key: "options", title: "" },
      ],
    };
  },

  components: {
    VFileUpload,
    VFileUploadItem,
  },

  mounted() {
    // set URL for production
    if (!import.meta.env.DEV) {
      this.url = location.href + "fileRequest.py";
    }

    // fetch initial file list
    this.fetchData({ task: "list" }, (data) => {
      this.fileList = data;
    });
  },

  computed: {
    filteredFiles() {
      if (!this.search) {
        return this.fileList;
      }
      const searchTerm = this.search.toLowerCase();
      return this.fileList.filter((file) => file.filename.toLowerCase().includes(searchTerm));
    },
  },

  methods: {
    fetchData(body, callback) {
      this.loading = true;
      this.checkedFiles = [];

      fetch(this.url, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(body),
      })
        .then((response) => response.json())
        .then((data) => {
          this.loading = false;
          if (data.status === "error") {
            this.errorTitle = "Error";
            this.errorMsg = data.message;
            this.dialog = true;
            this.snackbar = false;
            return;
          }
          callback(data);
        })
        .catch((error) => {
          this.loading = false;
          this.errorTitle = "Error";
          this.errorMsg = `An error occurred: ${error.message}`;
          this.dialog = true;
        });
    },
    createFolder(_event) {
      const folderName = prompt("Enter folder name:");
      if (!folderName) {
        return;
      }

      const body = {
        task: "create_folder",
        foldername: folderName,
        dir: this.currentDirectory.join("/"),
      };

      this.fetchData(body, (data) => {
        this.fileList = data.files;
        this.snackbar = true;
        this.log = `Folder "${folderName}" created successfully.`;
      });
    },
    changeDir(_event, dir) {
      if (dir === "..") {
        this.currentDirectory.pop();
      } else {
        this.currentDirectory.push(dir);
      }

      const body = {
        task: "list",
        dir: this.currentDirectory.join("/"),
      };

      this.fetchData(body, (data) => {
        this.fileList = data;
      });
    },
    deleteFile(_event, filename, isFolder) {
      filename = [filename];
      if (this.checkedFiles.length > 0) {
        filename = this.checkedFiles;
      }
      const body = {
        task: "delete",
        files: filename,
        dir: this.currentDirectory.join("/"),
      };

      this.fetchData(body, (data) => {
        this.fileList = data.files;
        this.snackbar = true;
        if (isFolder) {
          this.log = `Folder(s) deleted successfully.`;
        } else {
          this.log = `File(s) deleted successfully.`;
        }
      });
    },
    downloadFiles(_event, filenames) {
      filenames = [filenames];

      if (this.checkedFiles.length > 0) {
        filenames = this.checkedFiles;
      }

      const body = {
        task: "download",
        files: filenames,
        dir: this.currentDirectory.join("/"),
      };

      this.fetchData(body, (data) => {
        data.files.forEach((file) => {
          const link = document.createElement("a");
          link.href = file.content;
          link.download = file.filename;
          document.body.appendChild(link);
          link.click();
          document.body.removeChild(link);
          this.snackbar = true;
          this.log = `File(s) downloaded successfully.`;
        });
      });
    },
    uploadFiles(files) {
      const body = {
        task: "upload",
        dir: this.currentDirectory.join("/"),
        files: [],
      };

      const filesPromises = Array.from(files).map((file) => {
        return new Promise((resolve, reject) => {
          const fr = new FileReader();

          fr.onload = (event) => {
            const content = event.target.result.split(",")[1];
            const size = file.size;
            const type = file.type;

            body["files"].push({
              filename: file.name,
              content: content,
              filesize: size,
              filetype: type,
            });

            resolve();
          };

          fr.onerror = (e) => {
            console.error(`Error reading file ${file.name}:`, e);
            this.errorTitle = "File Read Error";
            this.errorMsg = `An error occurred while reading file ${file.name}: ${e.message}`;
            this.dialog = true;
            reject(e);
          };

          fr.readAsDataURL(file);
        });
      });

      Promise.all(filesPromises).then(() => {
        this.fetchData(body, (data) => {
          this.fileList = data.files;
          this.snackbar = true;
          this.log = `File(s) uploaded successfully.`;
        });
      });
    },
  },
};
</script>

<template>
  <!-- Upload Element-->
  <v-row class="ma-2">
    <v-file-upload
      @update:modelValue="uploadFiles($event)"
      clearable
      width="100%"
      multiple
      show-size
      density="compact"
      variant="compact">
    </v-file-upload>
  </v-row>

  <!-- Options-->
  <div class="d-flex align-center ma-2">
    <v-checkbox v-model="compact" label="Compact View" class="ma-2" hide-details density="compact"></v-checkbox>
    <v-btn class="ma-1" @click="createFolder($event)" title="Create Folder"
      ><v-icon icon="mdi-folder-plus"></v-icon
    ></v-btn>
    <v-btn disabled class="ma-1" title="Paste"><v-icon icon="mdi-content-paste"></v-icon></v-btn>
    <v-text-field
      v-model="search"
      label="Search"
      density="compact"
      prepend-inner-icon="mdi-magnify"
      variant="outlined"
      hide-details
      class="ma-2"
      max-width="25%"
      single-line></v-text-field>
  </div>

  <!--Path-->
  <v-row class="ma-2 path">
    <div>/</div>
    <div v-if="currentDirectory.length > 0" v-for="dir in currentDirectory">
      {{ dir }}/
    </div>
  </v-row>
  
  <v-progress-linear height="15" v-if="loading" indeterminate color="deep-purple accent-4"></v-progress-linear>
  
  <!-- File List Data-Table / Cards (compact-view) -->
  <v-row v-if="fileList.length > 0" class="ma-2">
    <!--v-card
      v-if="compact"
      v-for="file in filteredFiles"
      :title="file.filename"
      :subtitle="file.size + ' KB'"
      :text="file.created"
      :key="file.filename"
      :prepend-icon="file.isFolder ? 'mdi-folder' : typeIcons[file.filetype]"
      class="ma-2">
      <v-card-actions>
        <v-btn @click="downloadFiles($event, file.filename)" title="Download" icon class="mr-2">
          <v-icon icon="mdi-download"></v-icon>
        </v-btn>
        <v-btn @click="deleteFile($event, file.filename)" title="Delete" icon>
          <v-icon icon="mdi-delete"></v-icon>
        </v-btn>
        <v-btn @click="" title="Copy" icon>
          <v-icon icon="mdi-content-copy"></v-icon>
        </v-btn>
        <v-btn @click="" title="Move" icon>
          <v-icon icon="mdi-file-move"></v-icon>
        </v-btn>
      </v-card-actions>
    </v-card-->

    <v-card height="100%" width="100%">
      <v-data-table-virtual
        v-model:sort-by="sortBy"
        :headers="fileListHeaders"
        :items="fileList"
        :must-sort="true"
        :search="search"
        hide-default-footer
        :items-per-page="-1">
        <template v-slot:item="{ item }">
          <tr class="text-no-wrap">
            <td v-if="item.isFolder" class="text-blue font-weight-bold">
              <v-icon class="text-green" icon="mdi-folder"></v-icon
              ><v-btn @click="changeDir($event, item.filename)">{{ item.filename }}</v-btn>
            </td>
            <td v-else class="text-blue font-weight-bold">
              <v-icon class="text-white" :icon="typeIcons[item.filetype]"></v-icon> {{ item.filename }}
            </td>
            <td>{{ item.size }}</td>
            <td>{{ item.created }}</td>
            <td class="d-flex align-center justify-end">
              <v-btn
                v-if="!item.isFolder"
                @click="downloadFiles($event, item.filename)"
                title="Download"
                icon
                class="mr-2">
                <v-icon icon="mdi-download"></v-icon>
              </v-btn>
              <v-btn @click="deleteFile($event, item.filename, item.isFolder)" title="Delete" icon>
                <v-icon icon="mdi-delete"></v-icon>
              </v-btn>
              <v-btn @click="" title="Copy" icon>
                <v-icon icon="mdi-content-copy"></v-icon>
              </v-btn>
              <v-btn @click="" title="Move" icon>
                <v-icon icon="mdi-file-move"></v-icon>
              </v-btn>
              <v-checkbox title="Select" :value="item.filename" class="mt-5 ml-2" v-model="checkedFiles"></v-checkbox>
            </td>
          </tr>
        </template>
      </v-data-table-virtual>
    </v-card>
  </v-row>

  <!-- Snackbar for logs -->
  <v-snackbar width="100%" v-model="snackbar">
    {{ log }}
    <template v-slot:actions>
      <v-btn variant="text" @click="snackbar = false"> Close </v-btn>
    </template>
  </v-snackbar>

  <!-- Error Dialog -->
  <template>
    <div class="text-center pa-4">
      <v-dialog v-model="dialog" width="auto">
        <v-card max-width="600" prepend-icon="mdi-alert" :text="errorMsg" :title="errorTitle">
          <template v-slot:actions>
            <v-btn class="ms-auto" text="Ok" @click="dialog = false"></v-btn>
          </template>
        </v-card>
      </v-dialog>
    </div>
  </template>
</template>

<style>
.v-data-table__th {
  background-color: #311b92 !important;
  font-size: larger !important;
}

.v-card-title {
  color: #2196f3 !important;
}

.v-list-item {
  display: none !important; /* Hide the list items */
}

.v-table__wrapper {
  overflow: hidden !important; /* Disable table scrolling */
}

.path {
  font-family: monospace;
  font-size: 1em;
  background-color: black;
  color:greenyellow;
}
</style>
