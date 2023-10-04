import requests
from bs4 import BeautifulSoup
from colorama import Fore, init


class Parser:

    def __init__(self):
        self.headers = {'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, '
                                      'like Gecko) Chrome/47.0.2526.106 Safari/537.36'}

    def __get_soup(self, url: str) -> BeautifulSoup:
        page = requests.get(url, headers=self.headers)
        return BeautifulSoup(page.text, "html.parser")

    @staticmethod
    def __get_teams_data() -> list:
        res = []
        with open("teams_links.txt", 'r') as f:
            for _ in range(20):
                new_line: str = f.readline()[:-1]
                team_name, team_link = new_line.split(",")
                link_second_part: str = "/saison_id/2022/"
                res.append((team_name, team_link + link_second_part))
        return res

    def run(self) -> list:
        teams_data: list = self.__get_teams_data()

        data: list = []

        for i in range(len(teams_data)):
            team_name, team_link = teams_data[i]
            team_soup: BeautifulSoup = self.__get_soup(team_link)

            trs_odd: list = team_soup.find_all("tr", class_="odd")
            trs_even: list = team_soup.find_all("tr", class_="even")

            trs = []
            for j in range(len(trs_odd) + len(trs_even)):
                if j % 2 == 0:
                    trs.append(trs_odd.pop(0))
                else:
                    trs.append(trs_even.pop(0))

            for tr in trs:
                player_link: str = tr.find("td",
                                           class_="posrela").find("span",
                                                                  class_="show-for-small").find("a").get("href")

                data_new = self.__parse_player_page("https://www.transfermarkt.com" + player_link, team_name)
                if data_new:
                    data.append(data_new)
        return data

    def __parse_player_page(self, url: str, team_name: str) -> list:
        soup: BeautifulSoup = self.__get_soup(url)

        h1 = soup.find("h1", class_="data-header__headline-wrapper")
        full_name: str = h1.get_text(strip=True)
        full_name = ''.join(i for i in full_name if not i.isdigit() and i != "#").strip()
        surname: str = h1.find("strong").get_text(strip=True)
        name: str = full_name.replace(surname, "").strip()
        full_name = (name + " " + surname).strip()

        div = soup.find("div", class_="large-6 large-pull-6 small-12 columns spielerdatenundfakten")
        spans = div.find_all("span", class_="info-table__content info-table__content--bold")

        age = height = nation = position = foot = ""
        for i in range(len(spans)):
            k = i
            if any(char.isdigit() for char in spans[0].get_text(strip=True)):
                k += 1
            if k == 3:
                age: str = spans[i].get_text(strip=True)
            elif k == 4:
                height: str = spans[i].get_text(strip=True)[:-2]
            elif k == 5:
                try:
                    nation: str = spans[i].find("img").get("title").strip()
                except AttributeError:
                    print(Fore.YELLOW + "CHECK " + full_name)
                    return [full_name]
            elif k == 6:
                position: str = spans[i].get_text(strip=True)
            elif k == 7:
                foot: str = spans[i].get_text(strip=True)

        try:
            market_value: str = soup.find("div",
                                          class_="tm-player-market-value-development__current-value").get_text(
                strip=True)
        except AttributeError:
            market_value = ""
            print(Fore.YELLOW + "CHECK " + full_name)
            return [full_name]

        if position != "Goalkeeper":
            res = [full_name, team_name, age, height, nation, position, foot] + self.__get_player_stats(url) + [
                market_value]
            print(full_name + "++")
            return res
        return []

    def __get_player_stats(self, url: str) -> list:
        url_parts = url.split(r"/")
        stats_url: str = r"https://www.transfermarkt.com/" + url_parts[3] + r"/leistungsdatendetails/spieler/" + \
                         url_parts[-1] + r"/plus/0?saison=2022&verein=&liga=&wettbewerb=GB1&pos=&trainer_id="
        soup: BeautifulSoup = self.__get_soup(stats_url)
        tr = soup.find("tr", class_="odd")
        try:
            tds = tr.find_all("td", class_="zentriert")

            games = tds[1].get_text(strip=True)
            goals = tds[2].get_text(strip=True)
            assists = tds[3].get_text(strip=True)
            minutes_played = tr.find("td", class_="rechts").get_text(strip=True)

            return [games, goals, assists, minutes_played]
        except AttributeError:
            return ["-"] * 4
