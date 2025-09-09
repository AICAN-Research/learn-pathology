/**
 * Class for uploading multiple very large WSIs.
 * The files are uploaded in chunks.
 * A progress bar is created for ecah file to be uploaded.
 * The files are uploaded sequentially.
 */
class SlideUploader {
    constructor(files) {
        this.files = files;
        this.maxChunkSize = 1024 * 1024 * 8;

        // Calculate total nr of bytes to upload
        // and create progress bars for all files
        this.totalUploadSize = 0;
        this.totalUploaded = 0;
        for(let i = 0; i < this.files.length; ++i) {
            this.totalUploadSize += this.files[i].size;
            this.createProgressBar(i);
        }
    }

    startUpload() {
        this.startTime = new Date();
        // Upload one file at a time, start with file nr 0
        this.uploadChunk(null, 0, 0);
    }

    calculateETAAndSpeed() {
        let now = new Date();
        let durationSeconds = Math.round((now.getTime() - this.startTime.getTime()) / 1000);
        if(durationSeconds === 0)
            return null;

        let speed = this.totalUploaded / durationSeconds; // Bytes per second
        let ETAseconds = Math.floor((this.totalUploadSize - this.totalUploaded) / speed);

        let ETAhours = Math.floor(ETAseconds / 3600); // 60*60
        ETAseconds %= 3600;
        let ETAminutes = Math.floor(ETAseconds / 60);
        ETAseconds %= 60;

        let speedMB = speed / (1024*1024);

        return {ETAhours, ETAminutes, ETAseconds, speedMB};
    }

    createProgressBar(file_id) {
        let progressBarHTML = `
                        <div style="background: white; border-radius: 8px; padding: 10px; margin: 10px;">
                            <p class="filename_` + file_id + `">` + this.files[file_id].name + `</p>
                            <small class="textbox_` + file_id + `">Waiting to upload.</small>
                            <div class="progress" style="margin-top: 5px;">
                                <div class="progress-bar bg-success file_progress_bar_` + file_id + `" style="width: 0%"></div>
                            </div>
                        </div>
                        `;
        $('#uploads').html($('#uploads').html() + progressBarHTML);
    }

    uploadChunk(upload_id, file_id, chunkOffset) {
        let self = this;
        let nextChunkOffset = chunkOffset + this.maxChunkSize + 1;
        let currentChunk = this.files[file_id].slice(chunkOffset, nextChunkOffset);
        let uploadedChunkOffset = chunkOffset + currentChunk.size;

        let formData = new FormData();
        formData.append('file', currentChunk); // The actual data
        formData.append('filename', this.files[file_id].name);
        formData.append('finished', uploadedChunkOffset >= this.files[file_id].size ? 'true' : 'false');
        formData.append('upload_id', upload_id);

        $('.textbox_' + file_id).text("Uploading file ..");
        let info = this.calculateETAAndSpeed();
        let message = '<h2>Uploading, please wait.</h2>';
        if(info !== null) {
            message += '<h3>Speed: ' + info.speedMB.toFixed(1) + ' MB/s</h3>';
            message += '<h3>ETA: ';
            if (info.ETAhours > 0) {
                message += info.ETAhours + ' hours and ' + info.ETAminutes + ' minutes';
            } else if (info.ETAminutes > 0) {
                message += info.ETAminutes + ' minutes';
            } else {
                message += info.ETAseconds + ' seconds';
            }
            message += '</h3>';
        }
        $('#uploadInfo').html(message);

        $.ajaxSetup({
            headers: {
                "X-CSRFToken": document.querySelector('[name=csrfmiddlewaretoken]').value,
            }
        });

        $.ajax({
            url: '/slide/upload/',
            type: 'POST',
            dataType: 'json', // return data type
            cache: false,
            processData: false,
            contentType: false, // This must be false for some reason..
            data: formData,

            error: function (xhr) {
                $('.textbox_' + file_id).text('Error: ' + xhr.statusText);
            },

            success: function (res) {
                // Update progress
                self.totalUploaded += currentChunk.size;
                let percent = Math.round((uploadedChunkOffset / self.files[file_id].size) * 100);
                let element = $('.file_progress_bar_' + file_id);
                element.css('width', percent + '%');
                element.text(percent + '%');

                // Chunk was successfully uploaded
                if(nextChunkOffset < self.files[file_id].size) {
                    // Send next chunk
                    upload_id = res.upload_id;
                    self.uploadChunk(upload_id, file_id, nextChunkOffset);
                } else {
                    // Upload is complete
                    $('.textbox_' + file_id).text(res.data);
                    if(file_id + 1 < self.files.length) { // More files to send
                        // Start upload of new file
                        self.uploadChunk(null, file_id + 1, 0);
                    } else {
                        // All done
                        let button = `<a href="/slide/upload/process/" class="btn btn-success">Add uploaded slides to database</a>`;
                        $('#uploads').html(button + $('#uploads').html());
                        $('#uploadInfo').html('<h2>Upload Done!</h2>');
                    }
                }
            }
        });
    };
}

$(document).ready(function() {
    let g_pressed = false; // Make sure it is only pressed once

    $('#submit').on('click', (event) => {
        if(g_pressed)
            return;
        event.preventDefault();
        let files = $('#files').prop('files');
        let directoryFiles = $('#directories').prop('files');
        let allFiles = Array.from(files).concat(Array.from(directoryFiles));
        if(allFiles.length > 0) {
            let uploader = new SlideUploader(allFiles);
            uploader.startUpload();
            $('#upload-form').hide();
            g_pressed = true;
        }
    });
});
