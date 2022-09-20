import os
import time
from typing import Tuple

import requests

from tqdm import tqdm

class NetworkManager:

    """
    A class used to download links in a proper way. Implements a retry system (e.g. in case the connection fails), and a progress bar (by means of the tqdm library) for the link to retrieve.
    """

    def __init__(self):
        pass

    def __printResponseProgressBar(self, linkURL: str, response: requests.Response, chunkSize: int = 4):
        """The chunkSize defines the speed at which the response content is consumed, so it actually works as a bottleneck. The smaller, the slower."""

        with tqdm.wrapattr(open(os.devnull, "wb"), "write", miniters=1, position=1, leave=False, desc=linkURL.split("/")[-1].split("#")[0], total=int(response.headers.get("content-length", 0)), ncols=100) as fout:
            for chunk in response.iter_content(chunk_size=chunkSize):
                fout.write(chunk)

    def getLink(self, linkURL: str, printVerbose: bool = False, showRetries: bool = False, retries: int = 10, timeBetweenRetries: float = 0.5) -> Tuple[bool, str, bytes]:
        response: requests.Response = requests.Response()

        retriesCounter: int = retries
        again: bool = True
        while again:
            retriesCounter -= 1
            if retriesCounter == 0:
                break

            try:
                response = requests.get(linkURL, timeout=5, stream=printVerbose)
                responseContent: str = response.content     # DO NOT DELETE! This is necessary to fetch the response before printing the response in the progress bar and not be consumed.

                if printVerbose:
                    self.__printResponseProgressBar(linkURL, response)

                response.raise_for_status()

                again = False
            except:
                again = True

                if showRetries:
                    print("Trying again...\t(" + linkURL + ")")
                time.sleep(timeBetweenRetries)

        if response.status_code != 200:
            if retries > 1 and showRetries:
                print("Last try on...\t(" + linkURL + ")")

            try:
                response = requests.get(linkURL, timeout=5, stream=printVerbose)
                if printVerbose:
                    self.__printResponseProgressBar(linkURL, response)

                response.raise_for_status()
            except requests.exceptions.HTTPError as errh:
                return False, "HTTP Error: " + str(errh), response.content
            except requests.exceptions.ConnectionError as errc:
                return False, "Error Connecting: " + str(errc), response.content
            except requests.exceptions.Timeout as errt:
                return False, "Timeout Error: " + str(errt), response.content
            except requests.exceptions.RequestException as err:
                return False, "OOps: Something Else: " + str(err), response.content

        return True, "200 OK", response.content