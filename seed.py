from smse_backend.models import User, Model, Content, Embedding, Query, SearchRecord
from smse_backend import db
from smse_backend import create_app
import numpy as np


def set_users():
    user1 = User(username="saed", email="saed@example.com")
    user1.set_password("saed123")

    user2 = User(username="maher", email="maher@example.com")
    user2.set_password("maher123")

    user3 = User(username="aymon", email="aymon@example.com")
    user3.set_password("aymon123")

    user4 = User(username="adham", email="adham@example.com")
    user4.set_password("adham123")

    user5 = User(username="sherb", email="sherb@example.com")
    user5.set_password("sherb123")

    return [user1, user2, user3, user4, user5]


def set_models():
    model1 = Model(model_name="test_model1", modality=1)

    model2 = Model(model_name="test_model2", modality=2)

    model3 = Model(model_name="test_model3", modality=3)

    return [model1, model2, model3]


def set_embeddings(sample_models):
    embedding1 = Embedding(vector=np.random.rand(1024), model_id=sample_models[0].id)

    embedding2 = Embedding(vector=np.random.rand(1024), model_id=sample_models[1].id)

    embedding3 = Embedding(vector=np.random.rand(1024), model_id=sample_models[2].id)

    embedding4 = Embedding(vector=np.random.rand(1024), model_id=sample_models[0].id)

    embedding5 = Embedding(vector=np.random.rand(1024), model_id=sample_models[1].id)

    embedding6 = Embedding(vector=np.random.rand(1024), model_id=sample_models[2].id)

    embedding7 = Embedding(vector=np.random.rand(1024), model_id=sample_models[0].id)

    embedding8 = Embedding(vector=np.random.rand(1024), model_id=sample_models[1].id)

    embedding9 = Embedding(vector=np.random.rand(1024), model_id=sample_models[2].id)

    # The first six embeddins will be for the content and the last three will be for the query
    return [
        embedding1,
        embedding2,
        embedding3,
        embedding4,
        embedding5,
        embedding6,
        embedding7,
        embedding8,
        embedding9,
    ]


def set_contents(sample_users, sample_embeddings):
    content1 = Content(
        content_path="/test/path1/file.txt",
        content_tag=True,
        user_id=sample_users[0].id,
        embedding_id=sample_embeddings[0].id,
    )

    content2 = Content(
        content_path="/test/path2/file.txt",
        content_tag=False,
        user_id=sample_users[1].id,
        embedding_id=sample_embeddings[1].id,
    )

    content3 = Content(
        content_path="/test/path3/file.txt",
        content_tag=False,
        user_id=sample_users[2].id,
        embedding_id=sample_embeddings[2].id,
    )

    content4 = Content(
        content_path="/test/path4/file.txt",
        content_tag=True,
        user_id=sample_users[3].id,
        embedding_id=sample_embeddings[3].id,
    )

    content5 = Content(
        content_path="/test/path5/file.txt",
        content_tag=False,
        user_id=sample_users[4].id,
        embedding_id=sample_embeddings[4].id,
    )

    content6 = Content(
        content_path="/test/path6/file.txt",
        content_tag=True,
        user_id=sample_users[0].id,
        embedding_id=sample_embeddings[5].id,
    )

    return [content1, content2, content3, content4, content5, content6]


def set_queries(sample_users, sample_embeddings):
    query1 = Query(
        text="sample query1",
        user_id=sample_users[0].id,
        embedding_id=sample_embeddings[6].id,
    )

    query2 = Query(
        text="sample query2",
        user_id=sample_users[1].id,
        embedding_id=sample_embeddings[7].id,
    )

    query3 = Query(
        text="sample query3",
        user_id=sample_users[2].id,
        embedding_id=sample_embeddings[8].id,
    )

    return [query1, query2, query3]


def set_search_records(sample_contents, sample_queries):
    search_record1 = SearchRecord(
        similarity_score=0.95,
        content_id=sample_contents[5].id,
        query_id=sample_queries[0].id,
    )

    search_record2 = SearchRecord(
        similarity_score=0.85,
        content_id=sample_contents[1].id,
        query_id=sample_queries[1].id,
    )

    search_record3 = SearchRecord(
        similarity_score=0.75,
        content_id=sample_contents[2].id,
        query_id=sample_queries[2].id,
    )

    return [search_record1, search_record2, search_record3]


def main():
    app = create_app("DevelopmentConfig")

    with app.app_context():
        db.drop_all()
        db.create_all()

        sample_users = set_users()
        db.session.add_all(sample_users)
        db.session.commit()

        sample_models = set_models()
        db.session.add_all(sample_models)
        db.session.commit()

        smaple_embedings = set_embeddings(sample_models)
        db.session.add_all(smaple_embedings)
        db.session.commit()

        sample_contents = set_contents(sample_users, smaple_embedings)
        db.session.add_all(sample_contents)
        db.session.commit()

        sample_queries = set_queries(sample_users, smaple_embedings)
        db.session.add_all(sample_queries)
        db.session.commit()

        smaple_search_records = set_search_records(sample_contents, sample_queries)
        db.session.add_all(smaple_search_records)
        db.session.commit()


if __name__ == "__main__":
    main()
