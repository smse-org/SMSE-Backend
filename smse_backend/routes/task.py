from flask import Blueprint, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from celery.result import AsyncResult
from smse_backend.models import Task
from smse_backend import db
from datetime import datetime

# Create blueprint
task_bp = Blueprint("task", __name__)


@task_bp.route("/tasks", methods=["GET"])
@jwt_required()
def get_tasks():
    """
    Get all tasks for the current user.

    Returns:
        Response: JSON response containing task details
    """
    current_user_id = get_jwt_identity()

    # Get tasks from database
    tasks = Task.query.filter_by(user_id=current_user_id).all()

    # Format tasks for response
    formatted_tasks = []
    for task in tasks:
        # Check Celery task status
        celery_task = AsyncResult(task.task_id)

        try:
            # Attempt to get task status
            current_status = celery_task.status

            # Update task status in database if it has changed
            if current_status != task.status:
                task.status = current_status
                if current_status in ["SUCCESS", "FAILURE"]:
                    task.completed_at = datetime.now()
                    # Store task result if successful
                    if current_status == "SUCCESS":
                        try:
                            task.result = str(celery_task.result)
                        except Exception as e:
                            current_app.logger.error(
                                f"Error retrieving task result: {str(e)}"
                            )
                            task.result = "Error retrieving result data"
                db.session.commit()
        except Exception as e:
            current_app.logger.error(f"Error checking task status: {str(e)}")
            # Keep using the stored status if we can't fetch from Celery
            current_status = task.status

        # Add task to formatted list
        formatted_tasks.append(
            {
                "id": task.id,
                "task_id": task.task_id,
                "status": current_status,  # Use the variable we just determined
                "created_at": task.created_at,
                "completed_at": task.completed_at,
                "content_id": task.content_id,
                "result": task.result,
            }
        )

    return jsonify({"tasks": formatted_tasks}), 200


@task_bp.route("/tasks/<task_id>", methods=["GET"])
@jwt_required()
def get_task(task_id):
    """
    Get a specific task by ID for the current user.

    Args:
        task_id (str): ID of the task to retrieve

    Returns:
        Response: JSON response containing task details
    """
    current_user_id = get_jwt_identity()

    # Get task from database
    task = Task.query.filter_by(task_id=task_id, user_id=current_user_id).first()

    if not task:
        return jsonify({"message": "Task not found"}), 404

    # Check Celery task status
    celery_task = AsyncResult(task.task_id)

    try:
        # Attempt to get task status
        current_status = celery_task.status

        # Update task status in database if it has changed
        if current_status != task.status:
            task.status = current_status
            if current_status in ["SUCCESS", "FAILURE"]:
                task.completed_at = datetime.now()
                # Store task result if successful
                if current_status == "SUCCESS":
                    try:
                        task.result = str(celery_task.result)
                    except Exception as e:
                        current_app.logger.error(
                            f"Error retrieving task result: {str(e)}"
                        )
                        task.result = "Error retrieving result data"
            db.session.commit()
    except Exception as e:
        current_app.logger.error(f"Error checking task status: {str(e)}")
        # Keep using the stored status if we can't fetch from Celery
        current_status = task.status

    # Format task for response
    formatted_task = {
        "id": task.id,
        "task_id": task.task_id,
        "status": current_status,  # Use the variable we just determined
        "created_at": task.created_at,
        "completed_at": task.completed_at,
        "content_id": task.content_id,
        "result": task.result,
    }

    return jsonify({"task": formatted_task}), 200
