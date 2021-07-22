// #include <ctime>
#include <curl/curl.h>
#include <iostream>
#include <iomanip>
#include <string>
#include <thread>
#include <unistd.h>
#include <vector>
#include <wiringPi.h>
#include "curlpostrequest.h"
#include "mfrc522_delegate.h"

using namespace std;

#define LedPin 0

void
curl_thread_request(string additional_parameter)
{
    CurlPostRequest curlPostRequest = CurlPostRequest("http://localhost:8888");
    curlPostRequest.perform_post("/add/" + additional_parameter);
}


int main(int argc, char *argv[])
{

    bool read_only = false;

    if (argc > 1)
    {
        read_only = static_cast<bool>(static_cast<string>(argv[1]) == "--read=only");
    }

    if (read_only)
    {
        cout << "read only mode activated" << endl;
    }
    else
    {
        curl_global_init(CURL_GLOBAL_ALL);
    }

    if (wiringPiSetup() == -1)
    {
        cout << "Wiring Pi setup failed";
        return 1;
    }

    pinMode(LedPin, OUTPUT);
    digitalWrite(LedPin, HIGH);

    MFRC522_Delegate mfrc522_delegate = MFRC522_Delegate();
    MFRC522 mfrc = mfrc522_delegate.get_mfrc();

//    MFRC522 mfrc;
//    MFRC522::MIFARE_Key key;
//    byte sector = 1;
//    byte blockAddr = 4;

//    mfrc.setSPIConfig();
//    mfrc.PCD_Init();
//    byte trailerBlock   = 11;

//    MFRC522::StatusCode status;

//    byte buffer[32];
//    byte len = 32;
//    byte dataBlock[] = {
//        0x46, 0x65, 0x6c, 0x69,
//        0x78, 0x20, 0x45, 0x69,
//        0x73, 0x65, 0x6e, 0x6d,
//        0x65, 0x6e, 0x67, 0x65,
//        0x72, 0x00, 0x00, 0x00
//    };

    while (true)
    {
        if (!mfrc.PICC_IsNewCardPresent()) continue;
        if (!mfrc.PICC_ReadCardSerial()) continue;

        cout << "Detected something." << endl;

        try
        {
            mfrc522_delegate.uid_bytes_to_string(mfrc);

            thread th1(curl_thread_request, mfrc522_delegate.get_card_uid());

            digitalWrite(LedPin, LOW);

            mfrc522_delegate.halt_picc();

            if (th1.joinable())
            {
                th1.join();
            }

            digitalWrite(LedPin, HIGH);
        }
        catch (exception &err)
        {
            cout << "Error in while loop. " << err.what() << endl;
            break;
        }
    }

    curl_global_cleanup();
    return 0;
}
