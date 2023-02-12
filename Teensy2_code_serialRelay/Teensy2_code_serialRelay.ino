// this code is intended to use an arduino as an output relay. the idea here is to have an arduino receive serial bytes via serial1, 2 or 3 and send it to a PC via USB.
// this can be useful if you want to distribute serial information amoung multiple PCs or if USB communication of the primary device is already occupied by something else.

#define FirmwareVersion "0001" // This doesnt many anything here I would say, just copied from TouchShaker
#define moduleName "UARTSerialRelay" // Name of module for manual override UI and state machine assembler

#define MODULE_INFO 255  // returns module information
  
#define GOT_BYTE 14 // positive handshake for bpod commands
#define DID_ABORT 15 // negative handshake for bpod commands

unsigned long serialClocker = millis();
int FSMheader = 0;
bool midRead = false;
bool read_msg_length = false;
// float temp[50]; // temporary variable for general purposes

//
#define UART_SERIAL Serial2 // select which serial should be used for UART communication
int inByte = 0;

void setup() {
  // initialize both serial ports:
  Serial.begin(9600);
  UART_SERIAL.begin(115200);
}

void loop() {
  // read from port 1, send to port 0:
  if (UART_SERIAL.available()) {
    inByte = UART_SERIAL.read();
    Serial.write(inByte);
  }
}


void ReadSerialCommunication() {
  // Serial Communication over USB
  // Main purpose is to start a new trial
  if (Serial.available() > 0) {
    if (!midRead) {
      FSMheader = Serial.read();
      midRead = 1; // flag for current reading of serial information
      serialClocker = millis(); // counter to make sure that all serial information arrives within a reasonable time frame (currently 100ms)
      read_msg_length = false;
    }
    
    if (FSMheader == MODULE_INFO) { // return module information to bpod
      returnModuleInfo();
      midRead = 0;
    }
    else if (FSMheader == GOT_BYTE){
      midRead = 0;
    }
    else {
      //flush the Serial to be ready for new data
      while (Serial.available() > 0) {
        Serial.read();
      }

      //send abort to request resend
      Serial.write(DID_ABORT); midRead = 0;
    }
  }

  if (midRead && ((millis() - serialClocker) >= 100)) {
      //flush the Serial to be ready for new data
      while (Serial.available() > 0) {
        Serial.read();
      }

      //send abort to request resend
      Serial.write(DID_ABORT); midRead = 0;
  }
}

void returnModuleInfo() {
  Serial.write(65); // Acknowledge
  Serial.write(FirmwareVersion); // 4-byte firmware version
  Serial.write(sizeof(moduleName)-1); // Length of module name
  Serial.print(moduleName); // Module name
  Serial.write(0); // 1 if more info follows, 0 if not
}
