import array

import pymsteams
import pandas as pd


class Notify:
    """
    This class holds the functions to send message in teams.
    """

    def prepare_entity(self, name: str, email: str):
        """
        This function creates & formats the json
        entity with the name & email details.
        """
        entity = {
            "type": "mention",
            "text": "{}{}{}".format("<at>", name, "</at>"),
            "mentioned": {"id": email, "name": name},
        }
        return entity

    def prepare_title(self, title: str):
        """
        This function creates & formats the json
        title with the title detail.
        """
        title = {
            "type": "Container",
            "items": [
                {
                    "type": "TextBlock",
                    "size": "Medium",
                    "weight": "Bolder",
                    "text": title,
                }
            ],
        }
        return title

    def prepare_assigners(self, combined_name: str):
        """
        This function creates & formats the json
        assigners with the assigners details.
        """
        title = {
            "type": "Container",
            "items": [{"type": "TextBlock", "text": combined_name}],
        }
        return title

    def prepare_table(self, dataframe: pd.DataFrame):
        """
        This function creates & formats the dataframe
        as in tabular format
        with the message & color code details.
        """
        columns = [{"type": "Table", "width": "auto"} for _ in dataframe.columns]
        header_row = {
            "type": "TableRow",
            "cells": [
                {
                    "type": "TableCell",
                    "items": [
                        {
                            "type": "TextBlock",
                            "weight": "Bolder",
                            "text": col,
                            "wrap": True
                        }
                    ]
                }
                for col in dataframe.columns
            ]
        }
        data_rows = [
            {
                "type": "TableRow",
                "cells": [
                    {
                        "type": "TableCell",
                        "items": [
                            {
                                "type": "TextBlock",
                                "text": str(value),
                                "wrap": True
                            }
                        ]
                    }
                    for value in row
                ]
            }
            for row in dataframe.itertuples(index=False, name=None)
        ]
        table = {
            "type": "Table",
            "columns": columns,
            "rows": [header_row] + data_rows
        }
        return table

    def prepare_messages(self, informations: list):
        """
        This function creates & formats the json message
        with the message & color code details.
        """
        body_messages = []
        for index in range(len(informations)):
            information = Information(informations[index])
            body_messages.append(
                {
                    "type": "Container",
                    "items": [
                        {
                            "type": "TextBlock",
                            "wrap": True,
                            "text": information.message,
                            "weight": "bolder",
                            "color": information.color_code,
                        }
                    ],
                }
            )
        return body_messages

    def prepare_contents(self, contents: dict):
        """
        This function creates & formats the json
        content with the contents details.
        """
        content = []
        for key in contents:
            content.append({"title": key, "value": contents[key]})
        content_data = {
            "type": "Container",
            "items": [{"type": "FactSet", "spacing": "large", "facts": content}],
        }
        return content_data

    def prepare_tabular_body(self, title: str, combined_name: str,
                             dataframe: pd.DataFrame, data: dict):
        """
        This function creates & formats the json
        body with the all the sub component details
        for a tabular format in Teams message.
        """
        notify_data = NotifyData(data)
        body = [
            self.prepare_title(title),
            self.prepare_assigners(combined_name),
            self.prepare_table(dataframe)
        ]
        body_messages = self.prepare_messages(notify_data.messages)
        for body_message in body_messages:
            body.append(body_message)
        return body

    def prepare_body(self, title: str, combined_name: str, data: dict):
        """
        This function creates & formats the json
        body with the all the sub component details.
        """
        notify_data = NotifyData(data)
        body = [
            self.prepare_title(title),
            self.prepare_assigners(combined_name),
            self.prepare_contents(notify_data.contents),
        ]
        body_messages = self.prepare_messages(notify_data.messages)
        for body_message in body_messages:
            body.append(body_message)
        return body

    def send_to_teams(self, url: str, notify_data: dict, assigners: array, title: str,
                      dataframe: pd.DataFrame = None):
        """
        This function creates & formats the json with
        the given details and
        sends the message in Teams to the given url.
        """
        try:
            my_teams_message = pymsteams.connectorcard(url)
            combined_name = ""
            entities = []
            for assigner in assigners:
                entities.append(
                    self.prepare_entity(assigner["name"], assigner["email"]))
                combined_name = "{}{}{}{}{}".format(
                    combined_name, "<at>", assigner["name"], "</at>", " "
                )
            if (dataframe is None):
                body = self.prepare_body(title, combined_name, notify_data)
            else:
                body = self.prepare_tabular_body(title, combined_name, dataframe,
                                                 notify_data)
            payload = {
                "type": "message",
                "wrap": True,
                "attachments": [
                    {
                        "contentType": "application/vnd.microsoft.card.adaptive",
                        "content": {
                            "type": "AdaptiveCard",
                            "body": body,
                            "$schema":
                            "http://adaptivecards.io/schemas/adaptive-card.json",
                            "version": "1.0",
                            "msteams": {"width": "Full", "entities": entities},
                        },
                    }
                ],
            }
            my_teams_message.payload = payload
            my_teams_message.send()
        except Exception as exc:
            raise exc


class NotifyData(object):
    """
    NotifyData holds the contents & messages to be sent in Teams.
    contents - This will hold key & value pairs which will be prepared in table
    format in the body of the message.
    informations - List of informations.
    """
    contents: dict = {}
    messages: list

    """
    Constructs the data.
    """

    def __init__(self, data: dict):
        if "contents" in data:
            self.contents = data["contents"]
        self.messages = data["messages"]


class Information(object):
    """
    This will hold the message and the respective color code.
    """
    message: str
    color_code: str = "default"

    """
    Constructs the data.
    """

    def __init__(self, data: dict):
        if "color_code" in data:
            self.color_code = data["color_code"]
        self.message = data["message"]
