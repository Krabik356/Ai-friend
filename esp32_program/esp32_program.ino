#include <driver/i2s.h>
#include <WiFi.h>
#include <HTTPClient.h>
#include <Adafruit_GFX.h>
#include <Adafruit_ST7735.h>
#include <ArduinoJson.h>


String id = "12d1h2871";


Adafruit_ST7735 tft = Adafruit_ST7735(8, 15, 16, 7, 48);
int screenLed = 7;
int leftEye[5];
int rightEye[5];
uint16_t purple;

void clearPrevEyes(){
  tft.fillRoundRect(leftEye[0], leftEye[1], leftEye[2], leftEye[3], leftEye[4], ST77XX_BLACK);
  tft.fillRoundRect(rightEye[0], rightEye[1], rightEye[2], rightEye[3], rightEye[4], ST77XX_BLACK);
}

void setNewEyes(uint16_t color, int newLeftEye[5], int newRightEye[5]){
  for(int i =0;i<5;i++){
    leftEye[i] = newLeftEye[i];
    rightEye[i] = newRightEye[i];
  }

  tft.fillRoundRect(newLeftEye[0], newLeftEye[1], newLeftEye[2], newLeftEye[3], newLeftEye[4], color);
  tft.fillRoundRect(newRightEye[0], newRightEye[1], newRightEye[2], newRightEye[3], newRightEye[4], color);
}

void normal(){
  clearPrevEyes();
  int left[] = {30, 20, 30, 40, 10};
  int right[] = {98, 20, 30, 40, 10};
  setNewEyes(purple, left, right);
}

void friendly(){
  clearPrevEyes();
  int left[] = {25, 15, 40, 50, 10};
  int right[] = {93, 15, 40, 50, 10};
  setNewEyes(purple, left, right);
}

void listening(){
  clearPrevEyes();
  int left[] = {25, 25, 40, 30, 10};
  int right[] = {93, 25, 40, 30, 10};
  setNewEyes(purple, left, right);
}

void thinking(){
  clearPrevEyes();
  int left[] = {20, 10, 50, 20, 10};
  int right[] = {88, 10, 50, 20, 10};
  setNewEyes(purple, left, right);
}

void sad(){
  clearPrevEyes();
  int left[] = {93, 25, 40, 30, 10};
  int right[] = {25, 15, 40, 50, 10};
  setNewEyes(purple, left, right);
}

void rude(){
  clearPrevEyes();
  int left[] = {35, 30, 20, 20, 5};
  int right[] = {93, 30, 20, 20, 5};
  setNewEyes(purple, left, right);
}


HTTPClient client;
int sendButton = 21;

void setFaceByReputation(){
  client.begin("http://192.168.0.103:8000/user/reputation");
    client.addHeader("id", id);
    client.addHeader("Content-Type", "application/json");
    int code5 = client.GET();
    
    if(code5 == 200){
      JsonDocument doc;
      String strReputation = client.getString();
      deserializeJson(doc, strReputation);

      int reputation = doc["reputation"];
      if (reputation >= 50 && reputation <= 70) {
          normal();
      }
      else if (reputation >= 70 && reputation <= 90) {
          normal();
      }
      else if (reputation >= 90 && reputation <= 100) {
          friendly();
      }
      else if (reputation >= 40 && reputation <= 50) {
          sad();
      }
      else if (reputation >= 0 && reputation <= 40) {
          rude();
      }

    }else{
      normal();
    }

    client.end();
}


i2s_driver_config_t microCfg = {
  .mode=(i2s_mode_t)(I2S_MODE_MASTER | I2S_MODE_TX),
  .sample_rate = 22050,
  .bits_per_sample = I2S_BITS_PER_SAMPLE_16BIT,
  .channel_format = I2S_CHANNEL_FMT_ONLY_RIGHT,
  .communication_format = I2S_COMM_FORMAT_I2S,
  .intr_alloc_flags = ESP_INTR_FLAG_LEVEL1,
  .dma_buf_count = 8,
  .dma_buf_len = 512,
  .use_apll = false,
  .tx_desc_auto_clear = true,
  .fixed_mclk = 0
};

i2s_pin_config_t microPins = {
  .bck_io_num = 10,
  .ws_io_num = 9,
  .data_out_num = 11,
  .data_in_num = I2S_PIN_NO_CHANGE
};

i2s_driver_config_t speakerCfg = {
  .mode=(i2s_mode_t)(I2S_MODE_MASTER | I2S_MODE_RX),
  .sample_rate = 16000,
  .bits_per_sample = I2S_BITS_PER_SAMPLE_32BIT,
  .channel_format = I2S_CHANNEL_FMT_ONLY_LEFT,
  .communication_format = I2S_COMM_FORMAT_I2S,
  .intr_alloc_flags = ESP_INTR_FLAG_LEVEL1,
  .dma_buf_count = 8,
  .dma_buf_len = 512,
  .use_apll = false,
  .tx_desc_auto_clear = false,
  .fixed_mclk = 0
};

i2s_pin_config_t speakerPins = {
  .bck_io_num = 12,
  .ws_io_num = 18,
  .data_out_num = I2S_PIN_NO_CHANGE,
  .data_in_num = 13
};

void setup() {
  WiFi.begin("Name", "Password");
  while(WiFi.status() != WL_CONNECTED){
    delay(1000);
  }
  client.begin("http://192.168.0.103:8000/user/register");
  client.addHeader("id", id);
  client.GET();
  client.end();

  i2s_driver_install(I2S_NUM_0, &microCfg, 0, NULL);
  i2s_set_pin(I2S_NUM_0, &microPins);
  i2s_zero_dma_buffer(I2S_NUM_0);

  i2s_driver_install(I2S_NUM_1, &speakerCfg, 0, NULL);
  i2s_set_pin(I2S_NUM_1, &speakerPins);
  i2s_zero_dma_buffer(I2S_NUM_1);

  pinMode(screenLed, OUTPUT);
  analogWrite(screenLed, 90);
  tft.initR(INITR_BLACKTAB);
  tft.setRotation(1);
  tft.fillScreen(ST77XX_BLACK);
  purple = tft.color565(111, 0, 255);
  setFaceByReputation();

  pinMode(sendButton, INPUT_PULLUP);
}

void loop() {
  if(!digitalRead(sendButton)){
    delay(30);
    while(!digitalRead(sendButton)){
      delay(30);
    }

    client.begin("http://192.168.0.103:8000/audio/start");
    client.addHeader("id", id);
    int code = client.GET();
    client.end();
    while(code != 201){
      delay(300);
      client.begin("http://192.168.0.103:8000/audio/start");
      client.addHeader("id", id);
      code = client.GET();
      client.end();
    }

    listening();
    int32_t buffer[512];
    int16_t *toSend = (int16_t*)ps_malloc(48000*sizeof(int16_t));
    size_t bytesRead;
    int offset = 0;

    while(digitalRead(sendButton)){
      i2s_read(I2S_NUM_1, buffer, sizeof(buffer), &bytesRead, portMAX_DELAY);
      int samples = bytesRead/sizeof(int32_t);
      bool isNullingOffset = false;

      for(int i = 0;i < samples; i++){
        if(offset+i >= 48000){
          client.addHeader("id", id);
          client.addHeader("Content-Type", "application/octet-stream");
          int code2 = client.POST((uint8_t*)toSend, offset*sizeof(int16_t));
          client.end();
          offset = 0;
          isNullingOffset = true;
        }
        toSend[offset+i] = buffer[i] >> 14;
      }
      if(!isNullingOffset){
        offset += samples;
      }

    }
    client.begin("http://192.168.0.103:8000/audio/record");
    client.addHeader("id", id);
    client.addHeader("Content-Type", "application/octet-stream");
    int code3 = client.POST((uint8_t*)toSend, offset*sizeof(int16_t));
    client.end();

    free(toSend);
    toSend = nullptr;

    i2s_zero_dma_buffer(I2S_NUM_0);

    thinking();
    client.begin("http://192.168.0.103:8000/audio/stop");
    client.setTimeout(60000);
    client.addHeader("id", id);
    int code4 = client.GET();

    normal();
    if(code4 == 200){
      NetworkClient *stream = client.getStreamPtr();
      long sentenseSize = 0;

      while(client.connected() || stream->available()){
        
        if(sentenseSize == 0){
          String stringSize = stream->readStringUntil('\n');
          stringSize.trim();
          sentenseSize = strtol(stringSize.c_str(), nullptr, 16);
          if(sentenseSize == 0){
            break;
          }
        }

        uint8_t buffer[512];

        size_t bytesAvaliable = stream->available();
        if (bytesAvaliable == 0) {
          delay(1);
          continue;
        }

        size_t bytesToRead = min((long)512, (sentenseSize-(int)bytesAvaliable >=0 ? (int)bytesAvaliable : sentenseSize));

        size_t readed = stream->readBytes(buffer, bytesToRead);
        if (readed == 0){
          continue;
        }

        size_t written;
        i2s_write(I2S_NUM_0, buffer, readed, &written, portMAX_DELAY);
        sentenseSize -= written;
        if(sentenseSize <= 0){
          String stringSize = stream->readStringUntil('\n');
        }
      }

    }
    i2s_zero_dma_buffer(I2S_NUM_1);
    i2s_zero_dma_buffer(I2S_NUM_0);
    client.end();

    setFaceByReputation();
  }
}




























































