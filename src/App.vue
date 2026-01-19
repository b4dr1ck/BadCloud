<script>
import { VFileUpload, VFileUploadItem } from "vuetify/labs/VFileUpload";

export default {
  name: "App",
  data() {
    return {
      checkedFiles: [],
      dialog: false,
      log: "",
      errorTitle: "",
      errorMsg: "",
      snackbar: false,
      loading: true,
      url: "http://127.0.0.1/fileRequest.py",
      fileList: [],
      search: "",
      fileListHeaders: [
        {
          key: "filename",
          title: "Filename",
        },
        { key: "size", title: "Size (KB)" },
        { key: "created", title: "Created" },
        { key: "options", title: "Options" },
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
          callback(data);
          this.loading = false;
          if (data.status === "error") {
            this.errorTitle = "Error";
            this.errorMsg = data.message;
            this.dialog = true;
          }
        })
        .catch((error) => {
          this.loading = false;
          this.errorTitle = "Error";
          this.errorMsg = `An error occurred: ${error.message}`;
          this.dialog = true;
        });
    },
    deleteFile(_event, filename) {
      filename = [filename];
      if (this.checkedFiles.length > 0) {
        filename = this.checkedFiles;
      }
      this.snackbar = true;
      const body = {
        task: "delete",
        files: filename,
      };

      this.fetchData(body, (data) => {
        this.fileList = data.files;
        this.log = `Files(s) deleted successfully.`;
      });
    },
    downloadFiles(_event, filenames) {
      filenames = [filenames];

      if (this.checkedFiles.length > 0) {
        filenames = this.checkedFiles;
      }

      this.snackbar = true;
      const body = {
        task: "download",
        files: filenames,
      };

      this.fetchData(body, (data) => {
        data.files.forEach((file) => {
          const link = document.createElement("a");
          link.href = file.content;
          link.download = file.filename;
          document.body.appendChild(link);
          link.click();
          document.body.removeChild(link);
          this.log = `File(s) downloaded successfully.`;
        });
      });
    },

    uploadFiles(files) {
      this.snackbar = true;
      const body = {
        task: "upload",
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
            this.loading = false;
            reject(e);
          };

          fr.readAsDataURL(file);
        });
      });

      Promise.all(filesPromises).then(() => {
        this.fetchData(body, (data) => {
          this.fileList = data.files;
          this.log = `File(s) uploaded successfully.`;
        });
      });
    },
  },
};
</script>

<template>
  <v-progress-linear height="15" v-if="loading" indeterminate color="deep-purple accent-4"></v-progress-linear>

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

  <!-- File List Table -->
  <v-row v-if="fileList.length > 0" class="ma-2">
    <v-card width="100%" title="Files on Cloud">
      <template v-slot:text>
        <v-text-field
          v-model="search"
          label="Search"
          density="compact"
          prepend-inner-icon="mdi-magnify"
          variant="outlined"
          hide-details
          single-line></v-text-field>
      </template>
      <v-data-table :headers="fileListHeaders" :items="fileList" :search="search" items-per-page="25">
        <template v-slot:item="{ item }">
          <tr class="text-no-wrap">
            <td class="text-blue font-weight-bold">{{ item.filename }}</td>
            <td>{{ item.size }}</td>
            <td>{{ item.created }}</td>
            <td class="d-flex align-center">
              <v-btn @click="downloadFiles($event, item.filename)" title="Download" icon class="mr-2">
                <v-icon icon="mdi-download"></v-icon>
              </v-btn>
              <v-btn @click="deleteFile($event, item.filename)" title="Delete" icon>
                <v-icon icon="mdi-delete"></v-icon>
              </v-btn>
              <v-checkbox title="Select" :value="item.filename" class="mt-5 ml-2" v-model="checkedFiles"></v-checkbox>
            </td>
          </tr>
        </template>
      </v-data-table>
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
        <v-card max-width="400" prepend-icon="mdi-alert" :text="errorMsg" :title="errorTitle">
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
}

.v-list-item {
  display: none !important; /* Hide the list items */
}
</style>
