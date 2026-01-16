<script>
import { VFileUpload } from "vuetify/labs/VFileUpload";

export default {
  name: "App",
  data() {
    return {
      loading: true,
      url: "http://127.0.0.1/fileRequest.py",
      fileList: [],
    };
  },

  components: {
    VFileUpload,
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
        });
    },
    uploadFiles(files) {
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
            reject(e);
          };

          fr.readAsDataURL(file);
        });
      });

      Promise.all(filesPromises).then(() => {
        this.loading = true;
        this.fetchData(body, (data) => {
          this.fileList = data.files;
        });
      });
    },
  },
};
</script>

<template>
  <v-progress-linear height="15" v-if="loading" indeterminate color="deep-purple accent-4"></v-progress-linear>

  <v-row>
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

  <v-row>
    <v-list width="100%" density="compact" v-if="fileList.length > 0">
      <v-list-subheader>Files on my Cloud</v-list-subheader>
      <v-list-item v-for="file in fileList" :key="file.filename" :value="file.filename" color="primary">
        <template v-slot:prepend>
          <v-icon icon="mdi-file-image"></v-icon>
        </template>
        <v-list-item-title v-text="file.filename + ' (' + file.size / 1000 + ' KB)'"></v-list-item-title>
        <template v-slot:append>
          <v-btn icon class="mx-1">
            <v-icon icon="mdi-download"></v-icon>
          </v-btn>
          <v-btn icon>
            <v-icon icon="mdi-delete"></v-icon>
          </v-btn>
        </template>
      </v-list-item>
    </v-list>
  </v-row>
</template>

<style></style>
