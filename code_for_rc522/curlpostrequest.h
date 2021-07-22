#ifndef CURLPOSTREQUEST_H
#define CURLPOSTREQUEST_H

#include <curl/curl.h>
#include <iostream>
#include <string>

using std::cout;
using std::endl;

using std::string;

class CurlPostRequest
{

private:
    CURL *easyhandle = curl_easy_init();
    CURLcode response;

    string base_url;

    static size_t read_function(char *bufptr, size_t size, size_t nmemb, void *ourpointer);

public:
    CurlPostRequest();
    CurlPostRequest(const string new_base_url);
    ~CurlPostRequest();

    void perform_post(const string path);
};

#endif // CURLPOSTREQUEST_H
