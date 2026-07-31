# docker run -d -p 8000:8000 --env-file .env -v ./data:/home/data egauch/learnpathology:v1.0
FROM python:3.11-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
    libgl1 \
    libopengl0 \
    libusb-1.0-0 \
    libgomp1 \
    libpng16-16 \
    libglib2.0-0 \
    libxcb-xinerama0 \
    libpocl2 \
    pocl-opencl-icd && \
    rm -rf /var/lib/apt/lists/*

RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    libturbojpeg0 && \
    rm -rf /var/lib/apt/lists/*

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

COPY entrypoint.sh ./
RUN chmod u+x ./entrypoint.sh

RUN useradd -m -r appuser

WORKDIR /app

RUN git clone -b deployment https://github.com/AICAN-Research/learn-pathology.git .

RUN pip install --no-cache-dir --upgrade pip && pip install --no-cache-dir -r requirements.txt  && pip install --no-cache-dir PyTurboJPEG==1.7.*

RUN mkdir /home/data
RUN chown -R appuser /home/data

USER appuser

EXPOSE 8000

ENTRYPOINT ["/entrypoint.sh"]