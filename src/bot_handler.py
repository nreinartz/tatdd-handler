import asyncio
from dataclasses import asdict
import logging
import requests

from models.models import ChatSession, QuerySession
from models.shared import QueryRequest, QueryProgress, QueryType, TrendType


class BotHandler:
    def __init__(self, api_base_url: str, sbf_base_url: str):
        self.sessions = {}
        self.api_base_url = api_base_url
        self.sbf_base_url = sbf_base_url

    def process_repeat_request(self, request_body, last_query_session: QuerySession) -> tuple[dict, QuerySession]:
        updated_parameters: QueryRequest = self.__extract_query_parameters(
            request_body, last_query_session.parameters
        )

        try:
            query = self.create_session(updated_parameters)
            query_session = QuerySession(
                query["uuid"], updated_parameters, last_query_session.chat_session)

            text_lines = [
                "Okay, I initiated a new analysis on the basis of your last one and the adjusted parameters:",
                f"\t🔹 Topics: {', '.join(updated_parameters.topics)}",
                f"\t🔹 Distance: {updated_parameters.distance}",
                f"\t🔹 Time range: 
                    {updated_parameters.start_year}-{updated_parameters.end_year}",
                "\nCollecting data, please wait ..."
            ]

            return {
                "text": "\n".join(text_lines),
                "closeContext": True
            }, query_session
        except Exception as e:
            logging.exception(e)
            return {
                "text": "Sorry, something went wrong. Please try again later.",
                "closeContext": True
            }, None

    def process_create_request(self, request_body) -> tuple[dict, QuerySession]:
        parameters: QueryRequest = self.__extract_query_parameters(
            request_body
        )

        chat_session = ChatSession(
            request_body["botName"],
            request_body["channel"],
            request_body["messenger"],
            self.sbf_base_url
        )

        try:
            query = self.create_session(parameters)
            query_session = QuerySession(
                query["uuid"], parameters, chat_session)

            text_lines = [
                "Okay, I started a trend analysis for you for the following parameters:",
                f"\t🔹 Topics: {', '.join(parameters.topics)}",
                f"\t🔹 Distance: {parameters.distance}",
                f"\t🔹 Time range: 
                    {parameters.start_year}-{parameters.end_year}",
                "\nCollecting data, please wait ..."
            ]

            return {
                "text": "\n".join(text_lines),
                "closeContext": True
            }, query_session
        except Exception as e:
            logging.exception(e)
            return {
                "text": "Sorry, something went wrong. Please try again later.",
                "closeContext": True
            }, None

    def process_citation_recommendation(self, request_body) -> tuple[dict, QuerySession]:
        parameters: QueryRequest = self.__extract_query_parameters(
            request_body
        )

        chat_session = ChatSession(
            request_body["botName"],
            request_body["channel"],
            request_body["messenger"],
            self.sbf_base_url
        )

        try:
            query = self.create_session(
                parameters, QueryType.CITATION_RECOMMENDATION)
            query_session = QuerySession(
                query["uuid"], parameters, chat_session)

            text_lines = [
                "Okay, I started a search for citation recommendations with the following parameters:",
                f"\t🔹 Topics: {', '.join(parameters.topics)}",
                f"\t🔹 Min citations: {parameters.min_citations}",
                f"\t🔹 Time range: 
                    {parameters.start_year}-{parameters.end_year}",
                "\nCollecting data, please wait ..."
            ]

            return {
                "text": "\n".join(text_lines),
                "closeContext": True
            }, query_session
        except Exception as e:
            logging.exception(e)
            return {
                "text": "Sorry, something went wrong. Please try again later.",
                "closeContext": True
            }, None

    def create_session(self, parameters: QueryRequest, query_type: QueryType = QueryType.COMPLETE):
        url = f"{self.api_base_url}/api/queries"
        parameters.query_type = query_type
        response = requests.post(url, json=asdict(parameters))
        return response.json()

    def get_query(self, uuid):
        url = f"{self.api_base_url}/api/queries/{uuid}"
        response = requests.get(url)
        return response.json()

    def get_query_summary(self, uuid):
        url = f"{self.api_base_url}/api/queries/{uuid}/summary"
        response = requests.get(url)
        return response.json()

    async def track_analysis_progress(self, query_session: QuerySession):
        handled_progress = {
            QueryProgress.ANALYSING_TRENDS: False,
            QueryProgress.CITATION_RETRIEVAL: False
        }

        while True:
            session = self.get_query_summary(query_session.uuid)

            for progress in handled_progress:

                if handled_progress[progress] or session["progress"] < progress:
                    continue

                handled_progress[progress] = True
                self.__process_progress(
                    query_session,
                    progress
                )

            if all(handled_progress.values()) or session["progress"] == QueryProgress.FAILED:
                break

            await asyncio.sleep(1)

    async def track_citrec_progress(self, query_session: QuerySession):
        while True:
            session = self.get_query_summary(query_session.uuid)

            if session["progress"] == QueryProgress.FINISHED:
                self.__process_citation_recommendation_results(query_session)
                break

            if session["progress"] == QueryProgress.FAILED:
                query_session.chat_session.send_message(
                    "Sorry, something went wrong. Please try again later.")
                break

            await asyncio.sleep(1)

    def __process_progress(self, query_session: QuerySession, progress: QueryProgress):
        if progress == QueryProgress.ANALYSING_TRENDS:
            self.__process_analysing_trends(query_session)
        if progress == QueryProgress.CITATION_RETRIEVAL:
            self.__process_trend_results(query_session)

            query_session.chat_session.send_message(
                f"For more results and insights into your chosen topic, [look here]({
                    self.api_base_url}/results/{query_session.uuid})"
            )

    def __process_analysing_trends(self, query_session: QuerySession):
        query = self.get_query(query_session.uuid)
        publication_count = sum(query["results"]["search_results"]["raw"])
        query_session.chat_session.send_message(
            f"Data retrieved. I found {
                publication_count} matching publications. Analysing Trends ..."
        )

    def __process_trend_results(self, query_session: QuerySession):
        query = self.get_query(query_session.uuid)

        if all(trend["type"] == TrendType.NONE for trend in query["results"]["trend_results"]["sub_trends"]):
            query_session.chat_session.send_message(
                "There is neither a positive nor a negative trend for your topic."
            )
            return

        trend_messages = [
            "Alright, I found the following trends for your topic:",
            "",
        ]

        # No enumerate, since we skip NONE trends
        counter = 1
        for trend in query["results"]["trend_results"]["sub_trends"]:
            if trend["type"] == TrendType.NONE:
                continue

            icon = "📈" if trend["type"] == TrendType.INCREASING else "📉"
            trend_name = "Uptrend" if trend["type"] == TrendType.INCREASING else "Downtrend"

            trend_messages.append(
                f"{counter}. {
                    icon} **{trend_name}** from {trend['start']} to {trend['end']}"
            )

            counter += 1

        trend_messages.append("")
        trend_messages.append(
            query["results"]["trend_results"]["trend_description"]
        )

        query_session.chat_session.send_message("\n".join(trend_messages))

        query_session.chat_session.send_message(
            f"{self.api_base_url}/api/queries/{query_session.uuid}/chart")

        query_session.chat_session.send_message(
            f"[\u200B]({self.api_base_url}/api/queries/{query_session.uuid}/chart)"
        )

    def __process_citation_recommendation_results(self, query_session: QuerySession):
        query = self.get_query(query_session.uuid)

        query_session.chat_session.send_message(
            "I found the following publications that might be suitable for your topic:"
        )

        lines = []

        for i, publication in enumerate(query["results"]["citation_results"]["publications"]):
            authors = publication["authors"][0] + \
                (", et. al." if len(publication["authors"]) > 1 else "")

            lines.append(
                f'*{i + 1}. "{publication["title"]}" ({authors}, int({publication["year"]}))*')
            lines.append(
                f"[Link to Paper](https://doi.org/{publication['doi']})")
            lines.append(
                f"Distance: {round(publication['distance'], 2)}, Citations: {int(publication['citations']) if publication['citations'] is not None else 'unknown'}")
            lines.append("--------------------------")

        query_session.chat_session.send_message("\n".join(lines))

    def __extract_query_parameters(self, request_body, overwrite: QueryRequest | None = None) -> QueryRequest:
        if "entities" not in request_body:
            return {}

        print(request_body)
        print(overwrite)

        config: QueryRequest = QueryRequest(
            query_type=QueryType.COMPLETE,
            topics=[],
            distance=0.11,
            start_year=1980,
            end_year=2022,
            min_citations=0
        ) if overwrite is None else overwrite

        entities = request_body["entities"]

        if "distance" in entities:
            config.distance = float(entities["distance"]["value"])

        if "yearRange" in entities:
            years = entities["yearRange"]["value"].split("-")
            config.start_year = int(years[0])
            config.end_year = int(years[1])
        else:
            if "startYear" in entities:
                config.start_year = int(entities["startYear"]["value"])

            if "endYear" in entities:
                config.end_year = int(entities["endYear"]["value"])

        if "minCitationCount" in entities:
            config.min_citations = int(entities["minCitationCount"]["value"])

        for topic_keyword in ["topics", "citrec", "trends"]:
            if topic_keyword in entities:
                config.topics = self.__parse_topics(
                    entities[topic_keyword]["value"])
                break

        return config

    # Could be done via regex, but this is more safe
    # ((?:,?\s*)("([^"]+?)"|[^",]+))*
    def __parse_topics(self, topics):
        keyword_phrases = []
        current_phrase = ""
        inside_quotes = False

        for char in topics:
            if char == "," and not inside_quotes:
                keyword_phrases.append(current_phrase.strip())
                current_phrase = ""
            elif char == "\"":
                inside_quotes = not inside_quotes
            else:
                current_phrase += char

        keyword_phrases.append(current_phrase.strip())

        return keyword_phrases
