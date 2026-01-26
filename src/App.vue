<script>
import { VFileUpload, VFileUploadItem } from "vuetify/labs/VFileUpload";

export default {
  name: "App",
  data() {
    return {
      totalSize: 0,
      currentDirectory: [],
      checkedFiles: [],
      typeIcons: {
        image: "mdi-file-image",
        text: "mdi-file-document",
        application: "mdi-application-cog",
        unknown: "mdi-file-question",
      },
      dialog: false,
      prompt: false,
      log: "",
      errorTitle: "",
      errorMsg: "",
      promptTitle: "",
      promptMsg: "",
      newPromptValue: "",
      promptCallback: null,
      promptCallbackParam: null,
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
        { key: "filetype", title: "Type" },
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
      this.fileList = data.files;
    });
  },

  computed: {},

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
          if (data.totalSize) {
            this.totalSize = data.totalSize;
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
    openPrompt(_event, type, param) {
      this.prompt = true;
      this.newPromptValue = "";
      switch (type) {
        case "rename_file":
          this.newPromptValue = param;
          this.promptTitle = "Rename File";
          this.promptMsg = "Enter the new filename:";
          this.promptCallback = this.renameFile;
          this.promptCallbackParam = param;
          break;
        case "create_folder":
          this.promptTitle = "Create Folder";
          this.promptMsg = "Enter the folder name:";
          this.promptCallback = this.createFolder;
          this.promptCallbackParam = null;
          break;
      }
    },
    renameFile(_event) {
      const body = {
        task: "rename_file",
        old_filename: this.promptCallbackParam,
        new_filename: this.newPromptValue,
        dir: this.currentDirectory.join("/"),
      };

      this.fetchData(body, (data) => {
        this.fileList = data.files;
        this.snackbar = true;
        this.log = `File "${this.promptCallbackParam}" renamed to "${this.newPromptValue}" successfully.`;
      });
    },
    createFolder(_event) {
      const body = {
        task: "create_folder",
        foldername: this.newPromptValue,
        dir: this.currentDirectory.join("/"),
      };

      this.fetchData(body, (data) => {
        this.fileList = data.files;
        this.snackbar = true;
        this.log = `Folder "${this.newPromptValue}" created successfully.`;
      });
    },
    changeDir(_event, dir, absoulte = false) {
      if (dir === "..") {
        this.currentDirectory.pop();
      } else {
        if (absoulte) {
          this.currentDirectory = this.currentDirectory
            .join("/")
            .split("/")
            .slice(0, this.currentDirectory.indexOf(dir) + 1);
        } else {
          this.currentDirectory.push(dir);
        }
      }

      const body = {
        task: "list",
        dir: this.currentDirectory.join("/"),
      };

      this.fetchData(body, (data) => {
        this.fileList = data.files;
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
          if (filename.length > 1) {
            this.log = `Folders deleted successfully.`;
            return;
          }
          this.log = `Folder ${filename} deleted successfully.`;
        } else {
          if (filename.length > 1) {
            this.log = `Files deleted successfully.`;
            return;
          }
          this.log = `File ${filename} deleted successfully.`;
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
        });
        if (filenames.length > 1) {
          this.log = `Files downloaded successfully.`;
          return;
        }
        this.log = `File ${filenames[0]} downloaded successfully.`;
      });
    },
    uploadFiles(files) {
      const body = {
        task: "upload",
        dir: this.currentDirectory.join("/"),
        files: [],
      };

      if (files.length === 0) {
        return;
      }

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

          if (files.length > 1) {
            this.log = `Files uploaded successfully.`;
            return;
          }

          this.log = `File ${files[0].name} uploaded successfully.`;
        });
      });
    },
    selectAllFiles(event) {
      if (event === false) {
        this.checkedFiles = [];
        return;
      }
      this.checkedFiles = this.fileList.map((file) => file.filename);
    },
    reloadPage(_event) {
      location.reload();
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
  <div class="d-flex align-center mx-2">
    <v-btn @click="openPrompt($event, 'create_folder')" class="ma-1" title="Create Folder"
      ><v-icon icon="mdi-folder-plus"></v-icon
    ></v-btn>
    <v-text-field
      v-model="search"
      label="Search in current directory"
      density="compact"
      prepend-inner-icon="mdi-magnify"
      variant="outlined"
      hide-details
      class="ma-2"
      max-width="25%"
      single-line></v-text-field>
  </div>

  <!-- Progress Bar-->
  <v-progress-linear height="16" v-if="loading" indeterminate color="deep-purple accent-4"></v-progress-linear>
  <v-spacer class="py-2" v-else></v-spacer>

  <!--Path-->
  <v-row class="ma-2 path">
    <div @click="changeDir($event, dir, true)">/</div>
    <div @click="changeDir($event, dir, true)" v-if="currentDirectory.length > 0" v-for="dir in currentDirectory">
      {{ dir }}/
    </div>
  </v-row>

  <!--DiskSpace Info-->
  <div class="d-flex">
    <pre class="mx-2"
      >{{ parseFloat(totalSize[0] / 1000000).toFixed(2) }} / {{ parseFloat(totalSize[1] / 1000000).toFixed(2) }} MB</pre
    >
    <v-progress-linear class="ma-2" :max="totalSize[1]" v-model="totalSize[0]"></v-progress-linear>
  </div>

  <!-- File List Data-Table -->
  <v-row v-if="fileList.length > 0" class="ma-2">
    <v-card height="100%" width="100%">
      <v-data-table-virtual
        v-model:sort-by="sortBy"
        :headers="fileListHeaders"
        :items="fileList"
        :must-sort="true"
        :search="search"
        hide-default-footer
        :items-per-page="-1">
        <!-- Table Header-->
        <template v-slot:headers="{ columns, isSorted, getSortIcon, toggleSort }">
          <tr>
            <!-- Last Column: "Select All Checkbox"-->
            <template v-for="column in columns" :key="column.key">
              <th v-if="column.key === 'options'" class="d-flex align-center justify-end">
                <p class="text-h6">All</p>
                <v-checkbox
                  @update:model-value="selectAllFiles($event)"
                  title="Select"
                  value="all"
                  class="mt-5"></v-checkbox>
              </th>
              <!-- Other Columns-->
              <th v-else class="text-purple-lighten-2 cursor-pointer" @click="toggleSort(column)">
                <div class="d-flex align-center">
                  <span class="me-2" v-text="column.title.toUpperCase()"></span>
                  <v-icon v-if="isSorted(column)" :icon="getSortIcon(column)" color="text-purple-lighten-2"></v-icon>
                </div>
              </th>
            </template>
          </tr>
        </template>
        <!-- Table Body-->
        <template v-slot:item="{ item }">
          <tr class="text-no-wrap">
            <!-- Filenames with Icon (Exception for Folder Object)-->
            <td v-if="item.isFolder" class="text-blue font-weight-bold">
              <v-icon class="text-green" icon="mdi-folder"></v-icon
              ><v-btn class="text-none text-green" @click="changeDir($event, item.filename)">{{ item.filename }}</v-btn>
            </td>
            <td @click="openPrompt($event, 'rename_file', item.filename)" v-else class="text-blue font-weight-bold">
              <v-icon class="text-white" :icon="typeIcons[item.filetype]"></v-icon>
              {{ item.filename }}
            </td>
            <td>{{ item.filetype }}</td>
            <td>{{ item.size }}</td>
            <td>{{ item.created }}</td>
            <!--Options-->
            <td class="d-flex align-center justify-end">
              <!--For Folders-->
              <template v-if="item.isFolder">
                <v-btn @click="changeDir($event, item.filename)" title="Enter" icon class="mr-2"
                  ><v-icon icon="mdi-location-enter"></v-icon
                ></v-btn>
                <v-btn
                  v-if="item.filename !== '..'"
                  @click="deleteFile($event, item.filename, item.isFolder)"
                  title="Delete"
                  icon>
                  <v-icon icon="mdi-delete"></v-icon>
                </v-btn>
                <v-btn
                  v-if="item.filename !== '..'"
                  @click="openPrompt($event, 'rename_file', item.filename)"
                  title="Rename"
                  icon>
                  <v-icon icon="mdi-rename"></v-icon>
                </v-btn>
                <v-checkbox title="Select" :value="item.filename" class="mt-5 ml-2" v-model="checkedFiles"></v-checkbox>
              </template>
              <!--For Files-->
              <template v-else>
                <v-btn @click="downloadFiles($event, item.filename)" title="Download" icon class="mr-2">
                  <v-icon icon="mdi-download"></v-icon>
                </v-btn>
                <v-btn @click="deleteFile($event, item.filename, item.isFolder)" title="Delete" icon>
                  <v-icon icon="mdi-delete"></v-icon>
                </v-btn>
                <v-btn @click="openPrompt($event, 'rename_file', item.filename)" title="Rename" icon>
                  <v-icon icon="mdi-rename"></v-icon>
                </v-btn>
                <v-checkbox title="Select" :value="item.filename" class="mt-5 ml-2" v-model="checkedFiles"></v-checkbox>
              </template>
            </td>
          </tr>
        </template>
      </v-data-table-virtual>
    </v-card>
  </v-row>
  <v-row v-else>
    <v-card class="ma-2 pa-4" width="100%">
      <div class="text-center text-h6">No files found.</div>
    </v-card>
  </v-row>

  <!-- Snackbar for logs -->
  <v-snackbar width="100%" v-model="snackbar" :text="log" timer>
    <template v-slot:actions>
      <v-btn variant="text" @click="snackbar = false"> Close </v-btn>
    </template>
  </v-snackbar>

  <!-- Error Dialog -->
  <template>
    <div class="text-center pa-4">
      <v-dialog v-model="dialog" width="auto">
        <v-card prepend-icon="mdi-alert" :text="errorMsg" :title="errorTitle">
          <template v-slot:actions>
            <v-btn class="ms-auto" text="Ok" @click="reloadPage()"></v-btn>
          </template>
        </v-card>
      </v-dialog>
    </div>
  </template>

  <!-- Prompt-->
  <template>
    <div class="text-center pa-4">
      <v-dialog min-width="300" v-model="prompt" width="auto">
        <v-card prepend-icon="mdi-information" :text="promptMsg" :title="promptTitle">
          <v-card-text class="py-0 ma-0">
            <v-text-field
              v-model="newPromptValue"
              label="New Value"
              variant="outlined"
              density="compact"
              hide-details></v-text-field>
          </v-card-text>
          <template v-slot:actions>
            <div>
              <v-btn
                class="ms-auto"
                text="Ok"
                @click="
                  promptCallback();
                  prompt = false;
                "></v-btn>
              <v-btn class="ms-auto" text="Cancel" @click="prompt = false"></v-btn>
            </div>
          </template>
        </v-card>
      </v-dialog>
    </div>
  </template>
</template>

<style>
.v-card-title {
  color: #2196f3 !important;
}

.v-list-item {
  display: none !important; /* Hide the list items */
}

.v-table__wrapper {
  overflow-y: hidden !important; /* Disable table scrolling */
}

.v-table__wrapper tr:nth-of-type(odd) {
  background-color: #1e1e1e !important;
}

.v-table__wrapper td:nth-of-type(1) {
  max-width: 300px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.v-table__wrapper td:nth-of-type(1):hover {
  cursor: pointer;
  text-decoration: underline;
}

.path {
  font-family: monospace;
  font-size: 1em;
  background-color: black;
  color: greenyellow;
}

.path div:hover {
  cursor: pointer;
  text-decoration: underline;
}

@media screen and (max-width: 600px) {
  .v-table__wrapper th:nth-of-type(2),
  .v-table__wrapper th:nth-of-type(3),
  .v-table__wrapper th:nth-of-type(4) {
    display: none;
  }

  .v-table__wrapper td:nth-of-type(2),
  .v-table__wrapper td:nth-of-type(3),
  .v-table__wrapper td:nth-of-type(4) {
    display: none;
  }

  .v-input {
    max-width: 100% !important;
  }
}
</style>
