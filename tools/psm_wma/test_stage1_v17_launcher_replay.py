import hashlib
import base64
import gzip
import unittest

from tools.psm_wma.stage1_v17_launcher_replay import AuthorityReplayError, ReplayBinding, _replace_once, replay_outer_payload

CANONICAL_BASE_GZIP_B64 = "H4sIAAAAAAACA7Q6a1fiyLbf/RWZnA8DM4B5k9iLta5to00fRQ86ovTtxVTqIdGQMKmg0mfOf7+7qpKQoP26fe/MaiRV+/2qvYvoun6cpZ9povGcxFHYTZN4o6F1vkizKN90szTNtRitE7ygmfZo9Pw3Gn2meJ1ToklYlqVLLaOPEX2CpT//7OI//9TCTU55T9f1vWi5SrNcQzwvv4aIU88pnxhO8rh8WCC+ACHKx3ueJuX3lJffeI4qWnwdrrIUU8739ibn51faQNP3ScQf9rN4f8WX86cl0veOzydnh6diLyDEYqEfejbGxEO2GdiU4j4KPdd3MLYc5PnIQa6+dzJSxNY82w+jZP8uyvW9i9ur9+djuZ6u8n2cJgTJ3dUGDJbY+t7R6fBQAEhhfge4XtOW3SXKaRahOPqM8ihNuoVEQHsyPB7dAGoLWHc0vdtN0m5GVzHCtJuG9xTnXBfrWHziNKO9RZo+8AuULwb7hD7uJ+s4LiH2tOo/BYvyPItCcBs/jmL6EkHTWRSDaL2Y8V5h08Fr1GAvT3Ea9wAeyMZx+jRI6CPN9PbecHwNCvxbBw3mR+fj49HJ/OT0/O3hqX4g/FJjWYMYn1/eXl4NzwSMueVVB9kCvCAyPp9Phhenh0fD+fnbD8Ojq8tdOqeH4xOxdiRQTo/mh6en6vE/e4fvDi+uhhNhdD1P05iXMbO/dROdR8vlOkdhTOc8XWeYziuXzoVLe6tNw0KaTlDft/quE/rUpwwZzMaIBn0bQXR5hkUwQSa27D5Y7B/a1YJyqqGMavmCQm4hnIs8s/bhw9YwStIkwiguUkoT8BsJHiU5TUQMgQ82Gl2GlBBKDoAkEIoybRHxHKQUuCTF6yUAa3lGKZfYCeQ1XkQxySD3U6apHOntTQ6nwhxSH5WpvdBzCMUpoS2dbj7EYTLZoOn159H9KoTnR7ycrMLlMR/dp0+nRx82s+nzgpzE1uw6eLq9maSwHoXT4GE2fXo8XZoxOTl+gPXFKDH4Dv7zt/BvTP/p5vPhenYSfyYn46dXaGy+SMN+a6Cp8S0ZPn8L/ztkML5EA1vjdDadmOHJ9eZ04+YzkGF2cmzcXn4ITt9z4PHhAU3dRXg08saXTxFeXnPAXZHlNcMAh2B9lIzv0cn1A5k+xzgK2M3nt+zsyH1AN2Pj1j6M2OVzf7QMNiDf+nb6FJ3f3/JRAn4T+Dez+MZ+C3LdRefRBwMvj0Hm75Bl8yVZJpvbabye3YxesYtJwA6fb61FHE6Hgt8qnJom2D4C/Rm2AhMvxyDPGGS7vgdbPYYxyH1zbM5Alxv79nkUAd8SzspB1n8JOkL/e2S/fQT5AG78SG4+3IOd89upu5otrz+T48A6Az30dudrkbxUkgCVJ3IzYbfLeIE3I28GXsTWH3y0zFl4EtwrKw7h+fnx1jrmN9a1haYTwBdSzWKwCkh4zcAyG2yBFhFYZjlekJvxIgRJwDMm0HDHcRBToenNJJ4dB4tbGyLGcp7PpLSjGv3ZAtsTBv/AU9ds9n7i4pM/hOZL/O5sI6yi5HpmSFo72NDrILqdjrPZ1H0QkUbeT4ySDrGuVzNrYXwBr7QD4K0MnFzH4DUeWlL2VEQVRILb1Bnkvhx5Z1eH1quwNkQi6Ag4EIEf+GwKXlvOFuH7cZ12PpuajziJGURMLjLvrCZfOL3OC75bGhBtZPrH1k72BxOqEUQVRJPw+tQEnubjTNnqM9Cyb6xgHb6PWbgMgGb8APSeQE6A2eLU7aLs9gpPlXX57aXyLdBbo6nUY11mRZPG+DFczlYzE3wbgW+TiQFRCRHsxjgOOIYYOTtyRMUzAJ6Rkw9P4i/4K8bvz0S8Wexfg0EVwb/++utHaAo4jaETEJ0DI3pHt+FftwuNCIvu1IojV1iaLVEsWw54/u62RxITp0IX+p04Sh4Eso38IESeaRse8R0DGYbvmzbzLGYBLYe4ju8aTPHdipehpy5fIMv1YMNn1HF9l9meh0MvQCQwfZPaBrbc0GUODQLDMbBvE58x6nmO5flBP2QoILZtwrlW17JB2LFDO+z3QzewHdPoY3HohpSabj90PAILodkPfReDCrbhIuKxsO8YLhy+1LGIWRB+En93+8bvbt0EiYwu05zC10Wer/jBvugXF+uwh9Pl/tPz06Yk2hN9pECIEkKff4LrLlyvJNjtQi9OaAJd4wpaw9dYoCyPGPQZfP/O2M+MYL/Z0Mx3WM5LgvNHsyd6cslFKdLoj4vlpodcv0+ZZfqejwPHD33fDiD6LNsygtD3UN9CHiHY8BAKTddxsRf0GWQBONNFmDioogotJo8kc3jSiifN6tlOzyxMCmKvMgqfQrLXO/QdwKaszKY2cz0zdPp20PdC6roksPue6QWmSzzsGn1osXBoB66BoanrW4T1fS+0ZKNH8AvqW5kvJH/N7plmL5BwIZia5xlaicCGvzhXCezu7ELDLZr/Mpd/Kky3VJcpWcciYGXf2yvD8wf6XkkQEbQSihah9nNNdI1eGKcwi0bCHt/dTdfxG241ApMizyIG8kPHd6wAe33TMLAJfqSehWzDINjpIx/Kj+fivuF4IVQ55lsGlCeq3LW1sjLd6yp/r5q7xGr6Qnr0Wd/BThCaDnH8wLds3LdNhCzf9UIhN7KJ4b1OqFkdacgCUfgNDzTBUG+hChtGSBjqE9vrO47DWNAniFIvCCyPhihAyMWBb/aZS4yi7MZlTf8hzbd4pdYvKdXUppBA1KFgcGQEnhuGBIModmCEgQV1wsH9Ppw3nvsFSg29zdC2XTsERU3bsZjpwQEFx1UAvoYTAZvgXRIyUBmY9C1sBAFGTt/AoRFgbDtGYVoCVec1laFqys051M55OM/zXNXN4szc+nzr7hqpemgbhmUww+uHiDDqBqbpWgwx5Nm2Ry0DgtWloRuil0Qa6toETnYoV7ZrOibxMXKlWmYY2r7tBoFjB55JwI5QX5HvM6i9nmGbFqw52A5oLZK6CVqKZ3Fm1ZfpEkWxsKwBRziI5Zv/9ddf4nSrAxEkj0DLsLyuEXRN68qyD4z+gWP/bvgHRhlOy2WUixzdZbXd+Tq3LdwPMOwuKefoToBjkJUeaLXqpFXBq6ng3d6AabLUfYLuq7PX3hveXAyProbvxIjc0neP4Kr5KU5Jze5oP9/6tBuXC9pLtqovKnk6wPOnu6Jv8nx5eJX8XeAv8iwMmctAYyOgrhXYpgepbJjUI6FhEuabzCAUSq+NGHFMDD2lQaHCBwY0lr7ebu/t4Rhxrl3m6ao1WSd5tKTDLEuz9oG2go09QpnGIExaGUXAGZYzFHGqEIo1CUSiO8rzFmSMgKH5OkvKi8aeSiG511vQ5wJU4YmeJ289onhNt4jqucfzOaGPHa16ipK09sQhpkrm2fzHCYkrzt7lfHR8drWFg8ynbUU1SVkqLt5aoix1NBajOz5Iee98Pnl3Pj69bR9I9zECcQrL6YomdVDtb00Cj8+Pz09Pz6fl89Hp+fBmeNSWyJKvwmdCnhYjaiNi8vKolPFyMjzZEfJAIOE45VQgvVFu0hMxFNC7dYyybXrpimZhFEYKS3QEBeihEGlVa6VhO5oB0SHMsEIZF+eMCP85+FD5WBKU95JU6P/vlrwA1TvjNKEdPaOrlEd5mm3kiJRvOzQDor4JK244hUKi8Gdr+mI/ROK7zlDMX27G6R0IkVG2XokyxetEqmkBbHAXCebrLP7O4eF1fEZzLA6o34Eh31+A4fj+bwfyQQHzfQW7/5ukEGYokQhQaQX+LsXXYJY0k/WzxkLuCFi+DquOEqd8mfIuy6C+P6WZmCGhPkSPDTt+A2HHHguGeN6DzH5hml3cykaV9NcWfDxyce3TlSp0xW1QpepWhybGVy0iIV6xB6wr/4j/y0igiThZSKX9f2SE5tnmQIN2gXIIUgjcXnkztc5ZFypgj69i2U9Q3lJJQp8xXeXaH0kkAN9JcFkSD4oMKwZkIOAXecXVeQQcwN7bByHXG9ikcodCxXujQY3KIinMx0+qeqSZlE+LEiXnQXUmyOWB/ANZmUWrQsJaeZAgBQWAgZGTP4Hr4NT8h7iHfwMl/kATZ0eUrGkdeRdB/6i3NZQQtUETUix/0tsHjUNKeIBmhVgfzYOu+amxD7QLkF8GxbdS+B0DFobS27v4v+q/Cmso5Cb3mrWhflMoTQiKTEf7a53msg4VHFdi+BZQLV3bYVAwqZCFnAAkrCgsqijVTQPitHd2K/uUe4XIaltZ5bu0lfrUY6ZO4TWx5ZmwRSjE2q70Io44jqKWFAslm5bYb+EFEt0DWAb242S9VPvVshBen3chBtju8pb29zmQQpk+qDmprp3yTkdmxt5rmu2o9ZpOtY2Pxiepz2qBflTfATj9dXV/RNda4heiivMwE4n+WtKV4BGXFhAS6QNdalRk/w7XO6i3S5TVuD7QTadqGlpRTpdldklVxEJJS5W2li5+XzTbL0oHUCrNCV9f2hgW/z/sC2Tb39RSVMmNUPCVMOpIcQs7F7ZoKCeRPx7Yn5Q7abLDjqzBLljMNFs0AdZDhLQq5G2t7qEVdHbFVtWcMfl7vqjqBVhbFJKyIRIlGbrB+pZ4LrZ3DSCX44jnzT4tB0FpRUM1Y1m6zmH2T9CKL1I4UVR5vFMdZCw7yJPRlSIjKpQmu1L1W3cWihrPoS1PSAyhdidma/Qk8lKu9GQnWGlYtZ6n43+27qq2s8rBemfa3C4a/IK+1P7nLyhLm4lrSdnrb/taRJZR0ngdQLQnb+rNtTKNBHxdwWZv/ULJd6PJi/ZbySPuIsDjcJqIn36lf7R1wtcr8eoE9COliI0xQQrS0WrDRDkdACOYfc8nt98aH94ATV6fHAQLxQyLbh7zjqa8W80xyk7CQCrw9MoUYg6AyaUX02cIQ/4CsieaPvGzti5N8zXw5TJNYB7TKwM1LCOa/YLtq3NFPf5LKwnFxCcoVNesyAi8oPhhLqm3eDmXfBVRlGuw3svAgEX2wqJQyl9ANmwIAA0sXBvhWo0YQ1+Pr+a2ehRjKyom1vYvA2DPq2X1VWwoeFbtsO/CaMiGv57gzW01a2MgX3zj9WW2u15NmcILmFcjpgGAwh/fiKj/bQBWEahCj2QRExVW1dF10oJo+A1ld48QGE9kIKcIeekxZ4QPWu0ilsCLsF2e2QcSVhQalWmN4HujrdQMULzZ0xNcPv6m3jkSL/mIl2MAv+D7qQNHzONgOL4WdxEEiAxquBeji6Fcp1n2cl3O/VLQq2xdl7v8IsKyIVypzKqn0kvMNaWBEiQGR00OdfUMXPWUXMpm4jaqSjF10ZFGoqoVL/i8gRwXyVXYVo95V3qsU7z2Il+30jsStV0OYu2yfynblf/OZb9SiiuOTSArDxFLuB4eRF+ioOXyR900DM9xxMQjrn11KdenEtj8JIAE01Ld4ucLTcWTGuHUheRWeGgQurJYNYhuxX4jsQFBjMyylLUUDdhJAELUXfqct1rPsgd6Fs2IwOiFKdkIxSIeJZBiCaat544gcrxOZIPzjjI1ij33xN3tYKBX14DzFdrEKRI3hyIYazdFwLDWVcqOcktfbEu+H2GqkLwm0r9VglQMtMPLK712MzVooPbk2htRQwfFaaiO2KY66m5JsDlK5VrellOBpuu9+zRKWs8FWmUYRYvGOW+3YbhSFm5EAJT7XwZ91/Zr/YVa1PvUxAbF2DI9M/Ad5PsUGcSgiPoWC1gfU9I3AowCM2CGbVis7yAbGZ5PDehFQl9/aYWd/qLIhtr1QVFFEDSlUOZkQB986SxVuwUPllG+kMGoq0vGMErIPH1KKCmbOWX46sCR7zr+H/csOKYoUW+dCtYZX0SrQldGBmWTIjl3aj3K380O5e9Gf/L3TncSputE0npxr9m8lK3fyYrzSuKVm9WD2Hz9wvMruhR+U/HIiGoXIPXXGW2aXN4SFdB1h9QvhN4iTofyqxjhoI2m6lKodh+uT8ASbw+P/jkfjY/Ozy5Oh1dDMQOJd3cl9N6e2B2NT+bH7y6hQmyHiJYtf1NwYU4T71teHU5OhlcABUDe3sXhZDi+mp9Px8OJWuvvvYUj6PJqcnihFnz1TmwdJlAxysg84nPpULDaVt9q9nnhokLh80t17VUBFgY6FhexdfuKE6g4Velf6wiMK51EWr+Jc0jhpxivVxElAzXUQDMskh/+ROI+msuJqiHotjUtMKvDnHKaPULHDcjiB8pIXCwf6L/rnaK6QAoLAjUGJYl2kbaVizN5753DYUzzQlBd189SOAuRdr/meVeIA7wI5RhOKXFdBHN9CnM2L5yngk47fDuS8xYcljAERgiq4R1AyZezC0UUm3Lab+04taM1HVjlqqIPiij8KrQbli5U+PpPCjkVr3MjOVnLF8J78lPaQD0fz9/9cXH8rsxiOIcNhVpPvFcjCIZqq1UxKG3aAU0XNIvkj34DGThFlYnk+7QNEv/TyrX+Jm4E8e/5K4K/lDTmcEgCHLmtlDacWvUlJadepSiyjB8JCgGE4Uh6vf+989hd765tICk6iYP1PmZnZmdnfjMOL6Dn4I5kAMzNmDsdm5kf6kn+gJsNkg4jDAsNctRMJT6jdjiBOPWU4QZcaaunNASrkzXJ9oQUZEjUSOnQ8HkOuzn8ePWe6/eXD+CH3T9Q9TFc0lz+BY+7aJCi0RicGeTaAygU8QEfaeVxhG0ZiBqZK8q0+EhABb3WHLaY8DhXCNlitl7HpqWW/aj0FSKwR5sRvjwszkVsyIQZ3vTa6Be383SStbOk3W2/87ZpWAX7FKZTWKCtlE3GWYrZUhVQREkSgtMWyvtF+8nkwimXAFMi2CAv9QuJGojWCXjrKBv45roRwE5jSINiD8VSfFBxp9uAmiXFTarkuybJvGN8xzzpGeUWDJuq/Aek9I3ug0uKu1yonSRWQ24FhkLL0yOwrIms8YNZLwh8VEhwa2QfPRMzvIJuGvomup2lannmUE+USMDxBZuplciwJvQZxwnzlydEnXLTopaOKMOVDVFjDRFuRD7x2js4hsSykvHzJ9HTKInkqRjI8MnT0boPwRaXfybpMsKsnrwZZEhYxNu2Kh4ZgHW8WpCK7Ykxcroa1lTYOGbR7v2l9K0Bptruym2rhsFndsv9EgusOXdwVU120Gw/iMDwqXmbZidewO7lnqJXub9kKHPw35bsYYfKvjfpZxFDYczHTUKcD+xzA558LRsEDbrYj8qglwr3meNYg8wlognPXM+8KgSTtDgI+Zu1EX3j/aniK3VxqwD47t00o6EDykog4LIvBdikXtYBME0ZTFhtxxbplxaBO2DCfh5eXnk+wn/ShG2wXSV0qyHY4Cl2q60fgpu4xPrpsZNe3JlElPMqJxMLjnOcTriMpNVaUcXYY5oQjpWL6YwLp++ns0Xa0pUhuYjwPb/d9rUz+awvB6bMKs6miXBsRAx2OlRmI4IHxk+JLdQDDzS+HnrYOHaXMzTONqsU86BWbQjL3Lu8edGdZLqYrXNRvtwpaWmTYm7Cra0BLhTLeMf8Gq8MiHGFEik4P0TSyskmBq/m2l4wlpxXoRpb7cCOd+Wr7redBvBWktWCyrjhnCkUKob4YUxVbMJw0OwIB9NNcqigkiJdRMQ5c2BkMU2xCzh9Y+0T6laCvUrnrQICKlczSBooZ64GyjtCPpICwzTFchY+pum8iR+qaFKDMxYjWthlUCLQxh6qCKRiVeXqmTM2BE2p4NeESIIATclhvsBCoDTE1+0tYViUm7Ddv4dft2A338y8qhvzupFNDTqxDQ1Sfaex3oos+ySDaGLSDqBMT96CJ5dLUM0s4u9/Xg2dxw0RzLpBoPF1sE4IiyEBh1TxaemN6c7whrAsYZZlCPT7FOsWuFL6PE/jpekx2PCaKTAgUsEJr8DdFLUu8obUs+U89treMZJ1cbgWVgEwx4TXw8tPHB4O//7pN/72+bqIKKtDSGJZFciWZXDgRaAb1g9g5mXzB5Ukscvl1gus4J8icfg1ba596HTLYwZ3pco72f+D0DKjYSDkB/w7EPTDKYHiuY6FHGqjyi/TuLkGi7XOi2t9beMzxfFWyX+w6gsw8PezpbAqsA3Mj8tLZug1K0Uo8s+LXOef13lZRRe5q590uZbOjpoDpjOIXBSJhwWXOToQFV70SUMoJ00hb7AriTdeWJOxnA32OPgm07DMTXKMFJjOrMtzsTST6w536re4zLXWV+NuZDvS9FEtE6CG3wyHv4Y3w0+8o7wSXfUZTKTTjBXATdvDv778fBvcAR3nJ11VM4VtJ9QW9M22DrZ1zjo9Os+URZBMeD4qMonQE7qpF0hg8tvO4O5Y/z7h302v1+n1eqOkdxqcx71uEJ/146D7HhztJOj2s5Po/LQP/6Juloz6yVnQOe9HcYZvj8Sno16Udjxfs0z9TYhSuT04TE611gX7K0Km1pQVqXnJFPEzePr/3yPd00TvsAyOvbGSdcooLAa7DjKgPQ6s5GjhlsXLVTQRNB1msnMlW3D/hSww4OJJLBnkfsnqaZ43vxppcKyeCOWLWQOpBUbXW6oz+J7XuvN1qS8wHpxV3xt4R346RS8gpKJHGfvrzPORb6wFBtNdalT0/ObnYBnBSXiRlRhVixUzg/MWLSMhFd9nXffVdq3or1bFcQbQcX7+DLwrHik9NwsMaeYqIJ18YVHGrV0X2ojSnTAa18W7meEVeeL1zYwE/QNBDNLrG5SZt3rlwALrLflm5vWCrV/An6K/FuTfyv+91i8YkNzgx4/4EXv+yLcVYvjHX/UxgAWTfUc7ptruySwGLcEq9iIK4SCEYxA7Yjg4gNFhiPsLQ6qGDUM0gGHoDaQlPPgPt3Hp5hZKAAA="


def sha(raw): return hashlib.sha256(raw).hexdigest()


class ReplayTest(unittest.TestCase):
    def canonical(self):
        source = gzip.decompress(base64.b64decode(CANONICAL_BASE_GZIP_B64))
        self.assertEqual((len(source), sha(source)), (18966, "8b0fad39857fb72e3a3eb317f4acf6f2d6e94e196935f52f07d6170e79c678dd"))
        parser_rows = (
            ("--formal-root", "9dd2fb8b63ccd6a3193eec7ab6584cc24a68a4a5", "08d5828cdb4c12afa3b798ff01826c91ceb8755a"),
            ("--cwd", "/disk/rl/psm_wma/.authority-root-materialization-9dd2fb8", "/proc/self/fd/8"),
            ("--index", "/disk/rl/psm_wma/.authority-root-materialization-9dd2fb8/.authority-root.index", "/proc/self/fd/8/.authority-root.index"),
            ("--bootstrap-project-root", "/disk/rl/psm_wma/.authority-root-materialization-9dd2fb8", "/proc/self/fd/8"),
            ("--adapter-blob-oid", "da782754b8e8efa0f3cae973aa68602dcda1c237", "4a51bddd15ec9a88883e3071cc550de85721599b"),
            ("--adapter-raw-sha256", "091ea62d0a8b48429c67100c1395e62a300dc47a8d8f65c7046ba00f8205b5e9", "87e22fac98e61ba9fbf5e0c1adaf3f620365f35a04a266576c5bce4b83e9e816"),
            ("--collection-module-blob-oid", "eefde4e5b5a0965bbdcaa5390b9286a4c77f2665", "4e9f51a52e822e7e57b67aa6ff5eaab8613566c1"),
            ("--collection-module-raw-sha256", "1b3353b0bd1342f1685062f962a7cbc1ba0dbf699bdc72c099ca470cb09cc340", "89eb3ee194f16665aea76ed4dcbaba803fc944d1e0b889d25be69d0831e68c67"))
        source_rows = (("9dd2fb8b63ccd6a3193eec7ab6584cc24a68a4a5", "08d5828cdb4c12afa3b798ff01826c91ceb8755a"), (".authority-root-materialization-9dd2fb8", ".authority-root-materialization-08d5828"), ("da782754b8e8efa0f3cae973aa68602dcda1c237", "4a51bddd15ec9a88883e3071cc550de85721599b"), ("62a7bbf5fcb609e52931639001e6db01df81f0de2a33afd41c0080eb8e903f68", "bec6a57aab61fd888ef0eedce37adce227a38a299a9faded53b252c8b5901702"), ("7538", "9406"), ("7e1c0ecc2161984a88ea0d0eae82f9f7ced709ca919f0302f74a3a068e08c9b8", "ccd8ee2772d666707c919e6a20376c997771b9ff068fe0432fdaa96c686ab097"), ("2427", "2336"), ("72777bd7305c760c48c069eafd068f1a538383a6fdb8d40258acf3d8fc3b7ae2", "1a9543ec3e7ef4f37b4948dde2a6a9532b13a8415291cceafd90b9692c028333"))
        return source, ReplayBinding("08d5828cdb4c12afa3b798ff01826c91ceb8755a", "docs/build/PSM-WMA_Local_Memory_v0.3.5_authority_root_launcher_payload_v0.8.py", "af19a9eb66ecaf8bd0b92a48ab1867f105026658", sha(source), len(source), parser_rows, source_rows, "--bootstrap-owner-root-fd", "8", 2336, "1a9543ec3e7ef4f37b4948dde2a6a9532b13a8415291cceafd90b9692c028333", 18875, "658e9b9e6f34964310d6e2a5519c3b70243971b5ef535d753192e3d59d1960b8")

    def test_canonical_v16_replay(self):
        source, binding = self.canonical()
        result = replay_outer_payload(base_source=source, binding=binding)
        self.assertEqual((len(result.parser_argv_bytes), result.parser_argv_sha256), (2336, binding.expected_parser_sha256))
        self.assertEqual((len(result.outer_payload_bytes), result.outer_payload_sha256), (18875, binding.expected_outer_sha256))

    def test_canonical_self_check_drifts_fail(self):
        source, binding = self.canonical()
        for offset in range(4, 8):
            rows = list(binding.source_replacements)
            old, new = rows[offset]
            rows[offset] = ("missing-" + old, new)
            changed = ReplayBinding(binding.formal_parent, binding.base_path, binding.base_blob_oid,
                binding.base_raw_sha256, binding.base_bytes, binding.parser_replacements, tuple(rows),
                binding.owner_fd_flag, binding.owner_fd_value, binding.expected_parser_bytes,
                binding.expected_parser_sha256, binding.expected_outer_bytes, binding.expected_outer_sha256)
            with self.assertRaisesRegex(AuthorityReplayError, "source_target"):
                replay_outer_payload(base_source=source, binding=changed)

    def test_relocated_guard_fails(self):
        raw = 'def boot(s):\n    pass\ndef main():\n    if len(raw)!=7538 or digest(raw)!="x": fail("bootstrap identity")\n'
        with self.assertRaisesRegex(AuthorityReplayError, "source_target"):
            _replace_once(raw, "7538", "9406")

    def test_canonical_identity_and_shape_failures(self):
        source, binding = self.canonical()
        bad_sha = ReplayBinding(binding.formal_parent, binding.base_path, binding.base_blob_oid, "0" * 64, binding.base_bytes, binding.parser_replacements, binding.source_replacements, binding.owner_fd_flag, binding.owner_fd_value, binding.expected_parser_bytes, binding.expected_parser_sha256, binding.expected_outer_bytes, binding.expected_outer_sha256)
        with self.assertRaisesRegex(AuthorityReplayError, "base_identity"):
            replay_outer_payload(base_source=source, binding=bad_sha)
        raw = source.replace(b"RAW =", b"BROKEN =", 1)
        bad = ReplayBinding(binding.formal_parent, binding.base_path, binding.base_blob_oid, sha(raw), len(raw), binding.parser_replacements, binding.source_replacements, binding.owner_fd_flag, binding.owner_fd_value, binding.expected_parser_bytes, binding.expected_parser_sha256, binding.expected_outer_bytes, binding.expected_outer_sha256)
        with self.assertRaisesRegex(AuthorityReplayError, "raw_shape"):
            replay_outer_payload(base_source=raw, binding=bad)

    def test_canonical_source_rows_zero_through_three_fail(self):
        source, binding = self.canonical()
        for offset in range(4):
            rows = list(binding.source_replacements); old, new = rows[offset]; rows[offset] = ("missing-" + old, new)
            changed = ReplayBinding(binding.formal_parent, binding.base_path, binding.base_blob_oid, binding.base_raw_sha256, binding.base_bytes, binding.parser_replacements, tuple(rows), binding.owner_fd_flag, binding.owner_fd_value, binding.expected_parser_bytes, binding.expected_parser_sha256, binding.expected_outer_bytes, binding.expected_outer_sha256)
            with self.assertRaisesRegex(AuthorityReplayError, "source_target"):
                replay_outer_payload(base_source=source, binding=changed)

    def test_canonical_table_extra_and_reorder_fail(self):
        source, binding = self.canonical()
        parser = binding.parser_replacements + (("--remote", "https://github.com/wxwy/psm_wma.git", "https://github.com/wxwy/psm_wma.git"),)
        changed = ReplayBinding(binding.formal_parent, binding.base_path, binding.base_blob_oid, binding.base_raw_sha256, binding.base_bytes, parser, binding.source_replacements, binding.owner_fd_flag, binding.owner_fd_value, binding.expected_parser_bytes, binding.expected_parser_sha256, binding.expected_outer_bytes, binding.expected_outer_sha256)
        with self.assertRaisesRegex(AuthorityReplayError, "parser_target"): replay_outer_payload(base_source=source, binding=changed)
        rows = tuple(reversed(binding.source_replacements))
        changed = ReplayBinding(binding.formal_parent, binding.base_path, binding.base_blob_oid, binding.base_raw_sha256, binding.base_bytes, binding.parser_replacements, rows, binding.owner_fd_flag, binding.owner_fd_value, binding.expected_parser_bytes, binding.expected_parser_sha256, binding.expected_outer_bytes, binding.expected_outer_sha256)
        with self.assertRaisesRegex(AuthorityReplayError, "source_target"): replay_outer_payload(base_source=source, binding=changed)

    def test_canonical_parent_bypass_fails(self):
        source, binding = self.canonical()
        changed = ReplayBinding("not-canonical", binding.base_path, binding.base_blob_oid, binding.base_raw_sha256, binding.base_bytes, binding.parser_replacements, binding.source_replacements, binding.owner_fd_flag, binding.owner_fd_value, binding.expected_parser_bytes, binding.expected_parser_sha256, binding.expected_outer_bytes, binding.expected_outer_sha256)
        with self.assertRaisesRegex(AuthorityReplayError, "base_identity"): replay_outer_payload(base_source=source, binding=changed)
    def binding(self, source, parser, outer, replacements=(("--cwd", "/old", "/new"),)):
        return ReplayBinding("p", "x", "o", sha(source), len(source), replacements,
            (("FORMAL=old", "FORMAL=new"),), "--bootstrap-owner-root-fd", "8",
            len(parser), sha(parser), len(outer), sha(outer))

    def fixture(self):
        base = b'FORMAL=old\nRAW=(b\'\'\'["--cwd","/old","--bootstrap-project-root","/old"]\'\'\',)\n'
        parser = b'["--cwd","/new","--bootstrap-project-root","/old","--bootstrap-owner-root-fd","8"]'
        outer = b'FORMAL=new\nRAW=(b\'\'\'["--cwd","/new","--bootstrap-project-root","/old","--bootstrap-owner-root-fd","8"]\'\'\',)\n'
        return base, parser, outer

    def test_round_trip(self):
        base, parser, outer = self.fixture()
        result = replay_outer_payload(base_source=base, binding=self.binding(base, parser, outer))
        self.assertEqual(result.outer_payload_bytes, outer)

    def test_wrong_adjacent_value_fails(self):
        base, parser, outer = self.fixture()
        binding = self.binding(base, parser, outer, (("--cwd", "/wrong", "/new"),))
        with self.assertRaisesRegex(AuthorityReplayError, "parser_target"):
            replay_outer_payload(base_source=base, binding=binding)

    def test_duplicate_old_values_are_flag_addressed(self):
        base, _, _ = self.fixture()
        parser = b'["--cwd","/new","--bootstrap-project-root","/new","--bootstrap-owner-root-fd","8"]'
        outer = b'FORMAL=new\nRAW=(b\'\'\'["--cwd","/new","--bootstrap-project-root","/new","--bootstrap-owner-root-fd","8"]\'\'\',)\n'
        binding = self.binding(base, parser, outer, (("--cwd", "/old", "/new"), ("--bootstrap-project-root", "/old", "/new")))
        self.assertEqual(replay_outer_payload(base_source=base, binding=binding).parser_argv_bytes, parser)

    def test_reordered_targets_fail(self):
        base, parser, outer = self.fixture()
        binding = self.binding(base, parser, outer, (("--bootstrap-project-root", "/old", "/new"), ("--cwd", "/old", "/new")))
        with self.assertRaisesRegex(AuthorityReplayError, "parser_target"):
            replay_outer_payload(base_source=base, binding=binding)

    def test_source_drift_fails(self):
        base, parser, outer = self.fixture()
        binding = self.binding(base, parser, outer)
        # Replace the sole source target with one absent from the frozen base.
        binding = ReplayBinding(binding.formal_parent, binding.base_path, binding.base_blob_oid,
            binding.base_raw_sha256, binding.base_bytes, binding.parser_replacements,
            (("MISSING=old", "FORMAL=new"),), binding.owner_fd_flag, binding.owner_fd_value,
            binding.expected_parser_bytes, binding.expected_parser_sha256,
            binding.expected_outer_bytes, binding.expected_outer_sha256)
        with self.assertRaisesRegex(AuthorityReplayError, "source_target"):
            replay_outer_payload(base_source=base, binding=binding)

    def test_existing_owner_fd_fails(self):
        base, parser, outer = self.fixture()
        base = base.replace(b'"--cwd"', b'"--bootstrap-owner-root-fd"', 1)
        binding = self.binding(base, parser, outer)
        with self.assertRaisesRegex(AuthorityReplayError, "owner_fd"):
            replay_outer_payload(base_source=base, binding=binding)
