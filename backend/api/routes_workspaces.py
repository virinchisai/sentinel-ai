from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
import uuid
from backend.auth.middleware import require_permission
from backend.auth.models import Workspace, Membership, User, get_session_factory
from backend.auth.workspaces import resolve_workspace
from backend.auth.audit import log_action

router = APIRouter(prefix="/workspaces", tags=["workspaces"])


class WorkspaceRequest(BaseModel):
    name: str = Field(min_length=1, max_length=100)


class MemberRequest(BaseModel):
    username: str


@router.get("")
def list_workspaces(user=Depends(require_permission("chat"))):
    resolve_workspace(user.id)
    with get_session_factory()() as db:
        return [
            {"id": w.id, "name": w.name, "owner_id": w.owner_id}
            for w in db.query(Workspace)
            .join(Membership, Workspace.id == Membership.workspace_id)
            .filter(Membership.user_id == user.id)
        ]


@router.post("")
def create(body: WorkspaceRequest, user=Depends(require_permission("use_tools"))):
    with get_session_factory()() as db:
        w = Workspace(id=str(uuid.uuid4()), name=body.name, owner_id=user.id)
        db.add(w)
        db.flush()
        db.add(Membership(workspace_id=w.id, user_id=user.id))
        db.commit()
        return {"id": w.id, "name": w.name}


@router.put("/{workspace_id}/members")
def add_member(
    workspace_id: str,
    body: MemberRequest,
    user=Depends(require_permission("use_tools")),
):
    with get_session_factory()() as db:
        w = db.get(Workspace, workspace_id)
        if not w or w.owner_id != user.id:
            raise HTTPException(403, "Only the workspace owner can manage membership")
        member = db.query(User).filter_by(username=body.username).first()
        if not member:
            raise HTTPException(404, "User not found")
        if not db.get(Membership, (workspace_id, member.id)):
            db.add(Membership(workspace_id=workspace_id, user_id=member.id))
            db.commit()
    log_action(user.id, "workspace.member.add", workspace_id, body.username)
    return {"status": "added"}


@router.delete("/{workspace_id}/members/{user_id}")
def remove_member(
    workspace_id: str, user_id: int, user=Depends(require_permission("use_tools"))
):
    with get_session_factory()() as db:
        w = db.get(Workspace, workspace_id)
        if not w or w.owner_id != user.id or user_id == user.id:
            raise HTTPException(403, "Only the owner can remove other members")
        db.query(Membership).filter_by(
            workspace_id=workspace_id, user_id=user_id
        ).delete()
        db.commit()
    return {"status": "removed"}
