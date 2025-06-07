from ulauncher.api.client.EventListener import EventListener
from ulauncher.api.shared.action.RenderResultListAction import RenderResultListAction
from ulauncher.api.shared.item.ExtensionResultItem import ExtensionResultItem
from ulauncher.api.shared.action.SetUserQueryAction import SetUserQueryAction
from ulauncher.api.shared.item.ExtensionSmallResultItem import ExtensionSmallResultItem
from ulauncher.api.shared.action.ExtensionCustomAction import ExtensionCustomAction
from anipy_api.provider import LanguageTypeEnum

from anipy_api.anime import Anime


class ItemEnterEventListener(EventListener):

    def reset(self, extension):
        '''Reset to keyword'''
        return SetUserQueryAction(f"{extension.preferences['keyword']} ")

    def search_anime(self, data, extension):
        '''Show search anime result to user'''
        output = []

        curr_list = int(data["curr_list"])

        if curr_list == -1:
            anime_name = data["anime_name"]
            curr_list = 1
            anime_search_result = extension.search_anime(anime_name, 1)
        else:
            anime_search_result = extension.show_anime_list(curr_list)

        # If no links are present
        if anime_search_result is None:
            return RenderResultListAction([
                ExtensionResultItem(
                    icon="images/icon.png",
                    name="No anime found by this name",
                    description="Please search again",
                    on_enter=self.reset(extension))
            ])

        # If error
        if isinstance(anime_search_result, str):
            return RenderResultListAction([
                ExtensionResultItem(
                    icon="images/icon.png",
                    name="Error : " + anime_search_result,
                    description="Please search again",
                    on_enter=self.reset(extension))
            ])

        # If Present
        if anime_search_result is not None:
            animes: list[Anime] = anime_search_result["animes"]
            is_next: bool = anime_search_result["next"]
            output = []

            if curr_list > 1:
                output.append(ExtensionResultItem(
                    icon="images/icon.png",
                    name="Previous anime",
                    description="Previous anime",
                    on_enter=ExtensionCustomAction({
                        "action": "search_anime",
                        "curr_list": curr_list - 1
                    }, keep_app_open=True)

                ))

            # If links are present
            for anime in animes:
                # Anime has both sub and dub
                if len(anime.languages) > 1:
                    output.append(ExtensionResultItem(
                        icon="images/icon.png",
                        name=f"{anime.name} {str(anime.languages).replace('{', '(').replace('}', ')')}",
                        description="Select anime",
                        on_enter=ExtensionCustomAction({
                            "action": "select_language",
                            "anime": anime,
                        }, keep_app_open=True)
                    ))
                else:
                    output.append(ExtensionResultItem(
                        icon="images/icon.png",
                        name=f"{anime.name} {str(anime.languages).replace('{', '(').replace('}', ')')}",
                        description="Select anime",
                        on_enter=ExtensionCustomAction({
                            "action": "search_episode",
                            "anime": anime,
                            "language": LanguageTypeEnum.SUB if
                            LanguageTypeEnum.SUB in anime.languages else
                            LanguageTypeEnum.DUB,
                            "list_start": -1,
                            "list_end": -1
                        }, keep_app_open=True)
                    ))

            # Show next
            if is_next is True:
                output.append(ExtensionResultItem(
                    icon="images/icon.png",
                    name="Next anime",
                    description="Next anime",
                    on_enter=ExtensionCustomAction({
                        "action": "search_anime",
                        "curr_list": curr_list + 1
                    }, keep_app_open=True)
                ))

        return RenderResultListAction(output)

    def select_language(self, data):
        '''Show select language option to user'''

        anime = data["anime"]
        language = list(anime.languages)
        output = []

        if LanguageTypeEnum.SUB in language:
            output.append(ExtensionResultItem(
                icon="images/icon.png",
                name='Subbed',
                description="Select anime",
                on_enter=ExtensionCustomAction({
                    "action": "search_episode",
                    "anime": anime,
                    "language": LanguageTypeEnum.SUB,
                    "list_start": -1,
                    "list_end": -1
                }, keep_app_open=True)
            ))

        if LanguageTypeEnum.DUB in language:
            output.append(ExtensionResultItem(
                icon="images/icon.png",
                name='Dubbed',
                description="Select anime",
                on_enter=ExtensionCustomAction({
                    "action": "search_episode",
                    "anime": anime,
                    "language": LanguageTypeEnum.DUB,
                    "list_start": -1,
                    "list_end": -1
                }, keep_app_open=True)
            ))

        return RenderResultListAction(output)

    def search_episode(self, data, extension):
        '''Show episode list to user'''

        anime = data["anime"]

        list_start = data["list_start"]
        list_end = data["list_end"]

        # Initial settings
        if list_start == -1 and list_end == -1:
            list_start = 1

            anime.language = data["language"]
            extension.set_current_anime(anime)

            # Get max episode count
            max_episode = extension.get_anime_max_episode_no()

            # If max episode is str then show error
            if max_episode is None or isinstance(max_episode, str):
                return RenderResultListAction([
                    ExtensionResultItem(
                        icon="images/icon.png",
                        name="No episode found for this anime",
                        description=max_episode,
                        on_enter=self.reset(extension))
                ])

            # If max episode is int set up list
            list_end = 16 if max_episode > 15 else max_episode + 1
            extension.set_current_anime_max_episode(max_episode)

        else:
            max_episode = extension.get_current_anime_max_episode()

        output = []

        # Open anime ep 1 if only 1 ep is present
        if max_episode == 1:
            data["episode"] = 1
            return self.open_episode(data, extension)

        # Show episode manual entry if its more than 1
        if max_episode > 1:
            output.append(
                ExtensionSmallResultItem(
                    icon="images/icon.png",
                    name="Open a particular episode",
                    on_enter=SetUserQueryAction(
                        f"{extension.preferences['keyword']} type episode number : ")
                ))

        # Episode list logic below

        # Show prev option after 1st list
        if list_start > 1:
            output.append(
                ExtensionSmallResultItem(
                    icon="images/icon.png",
                    name="Previous Episodes",
                    on_enter=ExtensionCustomAction({
                        "action": "search_episode",
                        "anime": anime,
                        "list_start": list_start - 15,
                        "list_end": list_start
                    }, keep_app_open=True)
                ))
        # Show last episodes option if all episode not listed in first list
        elif list_start == 1 and max_episode > list_end - 1:
            output.append(
                ExtensionSmallResultItem(
                    icon="images/icon.png",
                    name="Last Episodes",
                    on_enter=ExtensionCustomAction({
                        "action": "search_episode",
                        "anime": anime,
                        "list_start": (int(max_episode/15)*15)+1,
                        "list_end": max_episode + 1
                    }, keep_app_open=True)
                ))

        # List max 15 eps per list
        for episode in range(list_start, list_end):
            output.append(
                ExtensionSmallResultItem(
                    icon="images/icon.png",
                    name="Episode "+str(episode),
                    on_enter=ExtensionCustomAction({
                        "action": "open_episode",
                        "episode": episode,
                        "anime": anime
                    }, keep_app_open=True)))

        # Show next option if applicable
        if max_episode > list_end - 1:
            output.append(
                ExtensionSmallResultItem(
                    icon="images/icon.png",
                    name="Next Episodes",
                    on_enter=ExtensionCustomAction({
                        "action": "search_episode",
                        "anime": anime,
                        "list_start": list_end,
                        "list_end": list_end + 15
                        if max_episode >= list_end + 15 else max_episode + 1
                    }, keep_app_open=True)
                ))
        elif max_episode > 15:
            output.append(
                ExtensionSmallResultItem(
                    icon="images/icon.png",
                    name="First Episodes",
                    on_enter=ExtensionCustomAction({
                        "action": "search_episode",
                        "anime": anime,
                        "list_start": 1,
                        "list_end": 16 if max_episode > 15 else max_episode + 1
                        if max_episode >= list_end + 15 else max_episode + 1
                    }, keep_app_open=True)
                ))

        return RenderResultListAction(output)

    def open_episode(self, data, extension):
        '''Open episode or show error to user'''

        if data["action"] == "open_episode_direcly":
            anime: Anime = data["anime"]

            providers = extension.read_from_provider_file()

            providers_name = []
            for p in providers:
                providers_name.append(p["NAME"])

            if anime.provider not in providers_name:
                return RenderResultListAction([
                    ExtensionResultItem(
                        icon="images/icon.png",
                        name=f"Provider : {anime.provider} currently not avaiable",
                        description="Please search again",
                        on_enter=self.reset(extension))
                ])

            extension.set_current_anime(anime)

        is_open_episode = extension.open_episode_in_player(
            data["episode"],
            extension.preferences['player_path'],
            extension.preferences['video_quality']
        )

        if is_open_episode is not None and isinstance(is_open_episode, bool) and is_open_episode is False:
            return RenderResultListAction([
                ExtensionResultItem(
                    icon="images/icon.png",
                    name="Selected episode not available for this anime",
                    description="Please search again",
                    on_enter=self.reset(extension))
            ])

        if is_open_episode is not None and isinstance(is_open_episode, str):
            return RenderResultListAction([
                ExtensionResultItem(
                    icon="images/icon.png",
                    name="Error occurred while playing the video",
                    description="Error : " + is_open_episode,
                    on_enter=self.reset(extension))
            ])

        return None

    def open_anime_history(self, data, extension):
        '''Show selected anime history to user'''

        anime: Anime = data["anime"]
        providers = extension.read_from_provider_file()

        providers_name = []
        for p in providers:
            providers_name.append(p["NAME"])

        if anime.provider not in providers_name:
            return RenderResultListAction([
                ExtensionResultItem(
                    icon="images/icon.png",
                    name=f"Provider : {anime.provider} currently not avaiable",
                    description="Please search again",
                    on_enter=self.reset(extension))
            ])

        extension.set_current_anime(anime)

        max_episode = extension.get_anime_max_episode_no()

        if isinstance(max_episode, str):
            return RenderResultListAction([
                ExtensionResultItem(
                    icon="images/icon.png",
                    name="Error while obtaining streaming link",
                    description="Please search again",
                    on_enter=self.reset(extension))
            ])

        if max_episode is None:
            return RenderResultListAction([
                ExtensionResultItem(
                    icon="images/icon.png",
                    name="Selected episode not available for this anime",
                    description="Please search again",
                    on_enter=self.reset(extension))
            ])

        extension.set_current_anime_max_episode(max_episode)
        episode = int(anime.episode)
        output = []

        if max_episode == 1:
            output.append(
                ExtensionSmallResultItem(
                    icon="images/icon.png",
                    name="Open " + anime.name,
                    on_enter=ExtensionCustomAction({
                        "action": "open_episode",
                        "episode": episode,
                    }, keep_app_open=True)
                )
            )

        else:
            # Next episode
            if episode + 1 <= max_episode:
                output.append(
                    ExtensionSmallResultItem(
                        icon="images/icon.png",
                        name="Open " + anime.name +
                        "'s next episode : " + str(episode + 1),
                        on_enter=ExtensionCustomAction({
                            "action": "open_episode",
                            "episode": episode + 1,
                        }, keep_app_open=True)
                    )
                )

            # Current episode
            output.append(
                ExtensionSmallResultItem(
                    icon="images/icon.png",
                    name="Open " + anime.name +
                    "'s current episode : " + str(episode),
                    on_enter=ExtensionCustomAction({
                        "action": "open_episode",
                        "episode": episode,
                    }, keep_app_open=True)
                )
            )

            # Previous episode
            if episode != 1:
                output.append(
                    ExtensionSmallResultItem(
                        icon="images/icon.png",
                        name="Open " + anime.name +
                        "'s previous episode : " + str(episode - 1),
                        on_enter=ExtensionCustomAction({
                            "action": "open_episode",
                            "episode": episode - 1,
                        }, keep_app_open=True)
                    )
                )

            # Any episode
            if max_episode != 1:
                output.append(
                    ExtensionSmallResultItem(
                        icon="images/icon.png",
                        name="Open a particular episode",
                        on_enter=SetUserQueryAction(
                            f"{extension.preferences['keyword']} type episode number : ")
                    )
                )

        # Delete entry
        output.append(
            ExtensionSmallResultItem(
                icon="images/icon.png",
                name="Delete this entry",
                on_enter=ExtensionCustomAction({
                    "action": "delete_item",
                    "anime": anime,
                    "delete_all": False
                }, keep_app_open=True)
            )
        )
        return RenderResultListAction(output)

    def delete_item(self, data, extension):
        '''Delete history based on input'''
        delete_all = data["delete_all"]

        if delete_all:
            extension.delete_item(delete_all)
        else:
            anime = data["anime"]
            extension.delete_item(delete_all, anime)

        return RenderResultListAction([
            ExtensionSmallResultItem(
                icon="images/icon.png",
                name="Deleted all items" if delete_all else "Deleted selected item",
                on_enter=self.reset(extension)
            )
        ])

    def update_provider(self, data, extension):
        '''Set the current provider'''
        provider = data["provider"]
        output = []
        if not provider["SELECTED"]:
            extension.update_provider(provider)
            output.append(
                ExtensionSmallResultItem(
                    icon="images/icon.png",
                    name="Provider updated",
                    on_enter=self.reset(extension)
                )
            )
        else:
            return RenderResultListAction([
                ExtensionSmallResultItem(
                    icon="images/icon.png",
                    name="Provider already selected",
                    on_enter=self.reset(extension)
                )
            ])

        return RenderResultListAction(output)

    def reset_provider(self, extension):
        '''Resets the provider list'''
        extension.reset_provider()

        return RenderResultListAction([
            ExtensionSmallResultItem(
                icon="images/icon.png",
                name="Provider reset successful",
                on_enter=self.reset(extension)
            )
        ])

    def on_event(self, event, extension):
        '''Event Handler'''
        data = event.get_data()

        if data["action"] == "search_anime":
            return self.search_anime(data, extension)

        # Select sub or dub
        if data["action"] == "select_language":
            return self.select_language(data)

        if data["action"] == "search_episode":
            return self.search_episode(data, extension)

        # Open episode link in default player
        if data["action"] == "open_episode" or data["action"] == "open_episode_direcly":
            return self.open_episode(data, extension)

        # Provider
        if data["action"] == "update_provider":
            return self.update_provider(data, extension)

        if data["action"] == "reset_provider":
            return self.reset_provider(extension)

        # History Related Below
        if data["action"] == "open_anime_history":
            return self.open_anime_history(data, extension)

        if data["action"] == "delete_item":
            return self.delete_item(data, extension)
