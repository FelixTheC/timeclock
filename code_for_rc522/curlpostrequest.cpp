#include "curlpostrequest.h"

CurlPostRequest::CurlPostRequest()
{
}

CurlPostRequest::CurlPostRequest(const string new_base_url)
{
    base_url = new_base_url;
}

CurlPostRequest::~CurlPostRequest()
{
    curl_easy_cleanup(easyhandle);
    easyhandle = nullptr;
}

void
CurlPostRequest::perform_post(const string path)
{
    const string tornado_url = base_url + path; //"http://localhost:8888/add/" + card_uid;
    //        const string json_data = "{\"user_id\": " + card_uid + ",\"username\": \"Some Name\"}";

    //        cout << "Sending Post request..." << endl;
    //        CURL *easyhandle = curl_easy_init();
    //        CURLcode response;

    if (easyhandle != nullptr)
    {
        curl_easy_setopt(easyhandle, CURLOPT_TIMEOUT, 1);
        curl_easy_setopt(easyhandle, CURLOPT_URL, tornado_url.c_str());
        curl_easy_setopt(easyhandle, CURLOPT_POST, 1);
        curl_easy_setopt(easyhandle, CURLOPT_READFUNCTION, read_function);
        curl_easy_setopt(easyhandle, CURLOPT_READDATA, nullptr);

        response = curl_easy_perform(easyhandle);

        if (response != CURLE_OK)
        {
            cout << "curl_easy_perform(easyhandle) failed: " << curl_easy_strerror(response) << endl;
        } else
        {
            cout << "Reached next point" << endl;
        }
    }
}

size_t
CurlPostRequest::read_function(char *bufptr, size_t size, size_t nmemb, void *ourpointer)
{
    return 1;
}


