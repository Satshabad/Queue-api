import unittest
import json

from ..queueapi import fix_lastfm_data

class DataTests(unittest.TestCase):

    maxDiff = None

    def test_fix_lastfm_data(self):
        expected = json.loads("""
        {
    "recenttracks": {
        "metadata": {
            "totalPages": "588",
            "total": "5876",
            "perPage": "10",
            "user": "fskhalsa",
            "page": "1"
            },
        "tracks": [
            {
                "album": {
                    "mbid": "38914b29-7788-4cff-80b7-1ced523f8675",
                    "name": "Back in Black"
                },
                "loved": "0",
                "streamable": "0",
                "name": "Hells Bells",
                "artist": {
                    "mbid": "66c662b6-6e2f-4930-8610-912e24c63ed1",
                    "name": "AC/DC",
                    "images": [
                        {
                            "url": "http://userserve-ak.last.fm/serve/34/35683175.jpg",
                            "size": "small"
                        },
                        {
                            "url": "http://userserve-ak.last.fm/serve/64/35683175.jpg",
                            "size": "medium"
                        },
                        {
                            "url": "http://userserve-ak.last.fm/serve/126/35683175.jpg",
                            "size": "large"
                        },
                        {
                            "url": "http://userserve-ak.last.fm/serve/252/35683175.jpg",
                            "size": "extralarge"
                        }
                    ]
                },
                "url": "http://www.last.fm/music/AC%2FDC/_/Hells+Bells",
                "images": [
                    {
                        "url": "http://userserve-ak.last.fm/serve/34s/81981459.jpg",
                        "size": "small"
                    },
                    {
                        "url": "http://userserve-ak.last.fm/serve/64s/81981459.jpg",
                        "size": "medium"
                    },
                    {
                        "url": "http://userserve-ak.last.fm/serve/126/81981459.jpg",
                        "size": "large"
                    },
                    {
                        "url": "http://userserve-ak.last.fm/serve/300x300/81981459.jpg",
                        "size": "extralarge"
                    }
                ],
                "mbid": "4f8c9450-4aef-4e76-a7b7-ca240b9e3c15",
                "date": {
                    "uts": "1364267224"
                }
            }
        ]
    }
}
        """.strip("\n"))

        data = json.loads("""{
    "recenttracks": {
        "@attr": {
            "totalPages": "588",
            "total": "5876",
            "perPage": "10",
            "user": "fskhalsa",
            "page": "1"},
        "track": [
            {
                "album": {
                    "mbid": "38914b29-7788-4cff-80b7-1ced523f8675",
                    "#text": "Back in Black"
                },
                "loved": "0",
                "streamable": "0",
                "name": "Hells Bells",
                "artist": {
                    "url": "AC/DC",
                    "mbid": "66c662b6-6e2f-4930-8610-912e24c63ed1",
                    "name": "AC/DC",
                    "image": [
                        {
                            "#text": "http://userserve-ak.last.fm/serve/34/35683175.jpg",
                            "size": "small"
                        },
                        {
                            "#text": "http://userserve-ak.last.fm/serve/64/35683175.jpg",
                            "size": "medium"
                        },
                        {
                            "#text": "http://userserve-ak.last.fm/serve/126/35683175.jpg",
                            "size": "large"
                        },
                        {
                            "#text": "http://userserve-ak.last.fm/serve/252/35683175.jpg",
                            "size": "extralarge"
                        }
                    ]
                },
                "url": "http://www.last.fm/music/AC%2FDC/_/Hells+Bells",
                "image": [
                    {
                        "#text": "http://userserve-ak.last.fm/serve/34s/81981459.jpg",
                        "size": "small"
                    },
                    {
                        "#text": "http://userserve-ak.last.fm/serve/64s/81981459.jpg",
                        "size": "medium"
                    },
                    {
                        "#text": "http://userserve-ak.last.fm/serve/126/81981459.jpg",
                        "size": "large"
                    },
                    {
                        "#text": "http://userserve-ak.last.fm/serve/300x300/81981459.jpg",
                        "size": "extralarge"
                    }
                ],
                "mbid": "4f8c9450-4aef-4e76-a7b7-ca240b9e3c15",
                "date": {
                    "uts": "1364267224",
                    "#text": "26 Mar 2013, 03:07"
                }
            }
        ]
    }
}""".strip("\n"))
        self.assertEqual(fix_lastfm_data(data), expected)

if __name__ == '__main__':
    unittest.main()
