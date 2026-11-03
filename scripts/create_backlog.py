"""Create the GitHub backlog for Deliverables Part-2 with the GitHub CLI (gh).

One-time setup (Windows):  winget install GitHub.cli   then   gh auth login   and   gh auth refresh -s project
Run from the repo folder:

    python scripts/create_backlog.py --dry-run     # print what would be created
    python scripts/create_backlog.py               # labels, milestones, issues, Project with Story Points + Sprint
    python scripts/create_backlog.py --close 1 2   # after the sprints: close the Sprint 1 and 2 issues, Status = Done

Creates: labels (sprint-1/2/3, story-points:N), milestones Sprint 1–3, one issue per story assigned to its owner,
and a GitHub Project "Team 13 - HAPRS Backlog" linked to the repo with Story Points and Sprint fields.
"""
import argparse
import json
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from backlog_data import OWNERS, SPRINTS, STORIES  # noqa: E402

REPO = "siddhardha-06/Healthcare-Appointment-Patient-Record-System"
OWNER = "siddhardha-06"
PROJECT_TITLE = "Team 13 - HAPRS Backlog"
DRY = False


def gh(*args, capture=True):
    cmd = ["gh", *args]
    if DRY:
        print("  $", " ".join(a if " " not in a else f'"{a}"' for a in cmd))
        return ""
    res = subprocess.run(cmd, capture_output=capture, text=True)
    if res.returncode != 0:
        raise SystemExit(f"gh failed: {' '.join(cmd)}\n{res.stderr}")
    return res.stdout.strip()


def ensure_labels():
    for n in (1, 2, 3):
        gh("label", "create", f"sprint-{n}", "--repo", REPO, "--color", ["0e8a16", "1d76db", "5319e7"][n - 1], "--force")
    for sp in sorted({s[3] for s in STORIES}):
        gh("label", "create", f"story-points:{sp}", "--repo", REPO, "--color", "fbca04", "--force")
    gh("label", "create", "user-story", "--repo", REPO, "--color", "c5def5", "--force")


def ensure_milestones():
    existing = [] if DRY else json.loads(gh("api", f"repos/{REPO}/milestones?state=all"))
    have = {m["title"] for m in existing}
    for n, (title, due, desc) in SPRINTS.items():
        if title not in have:
            gh("api", f"repos/{REPO}/milestones", "-f", f"title={title}", "-f", f"due_on={due}T18:00:00Z",
               "-f", f"description={desc}")


def body(story):
    sid, title, reqs, sp, owner, sprint, accept = story
    return (f"**Story {sid}** – {title}\n\n**Requirements:** {reqs}\n**Story points:** {sp}\n"
            f"**Owner:** {owner}\n**Sprint:** {SPRINTS[sprint][0]}\n\n**Acceptance:** {accept}\n\n"
            f"Traceability: see docs/requirements-registry.md and docs/backlog/backlog.md")


def create_issues():
    urls = {}
    existing = {} if DRY else {i["title"]: i["url"] for i in json.loads(
        gh("issue", "list", "--repo", REPO, "--state", "all", "--limit", "200", "--json", "title,url"))}
    for s in STORIES:
        title = f"{s[0]}: {s[1]}"
        if title in existing:
            urls[s[0]] = existing[title]
            continue
        urls[s[0]] = gh("issue", "create", "--repo", REPO, "--title", title, "--body", body(s),
                        "--label", f"user-story,sprint-{s[5]},story-points:{s[3]}", "--assignee", OWNERS[s[4]],
                        "--milestone", SPRINTS[s[5]][0]) or f"<issue {s[0]}>"
    return urls


def setup_project(urls):
    projects = [] if DRY else json.loads(gh("project", "list", "--owner", OWNER, "--format", "json"))["projects"]
    proj = next((p for p in projects if p["title"] == PROJECT_TITLE), None)
    if proj is None:
        out = gh("project", "create", "--owner", OWNER, "--title", PROJECT_TITLE, "--format", "json")
        proj = json.loads(out) if out else {"number": 0, "id": "PROJECT_ID"}
        gh("project", "link", str(proj["number"]), "--owner", OWNER, "--repo", REPO)
        gh("project", "field-create", str(proj["number"]), "--owner", OWNER, "--name", "Story Points", "--data-type", "NUMBER")
        gh("project", "field-create", str(proj["number"]), "--owner", OWNER, "--name", "Sprint", "--data-type",
           "SINGLE_SELECT", "--single-select-options", "Sprint 1,Sprint 2,Sprint 3")
    num = str(proj["number"])
    fields = {} if DRY else {f["name"]: f for f in json.loads(gh("project", "field-list", num, "--owner", OWNER, "--format", "json"))["fields"]}
    for s in STORIES:
        item = gh("project", "item-add", num, "--owner", OWNER, "--url", urls[s[0]], "--format", "json")
        if DRY:
            continue
        item_id = json.loads(item)["id"]
        gh("project", "item-edit", "--id", item_id, "--project-id", proj["id"], "--field-id", fields["Story Points"]["id"],
           "--number", str(s[3]))
        opt = next(o["id"] for o in fields["Sprint"]["options"] if o["name"] == SPRINTS[s[5]][0])
        gh("project", "item-edit", "--id", item_id, "--project-id", proj["id"], "--field-id", fields["Sprint"]["id"],
           "--single-select-option-id", opt)
    print(f"Project #{num} ready: https://github.com/users/{OWNER}/projects/{num}")


def close_sprints(sprints):
    issues = json.loads(gh("issue", "list", "--repo", REPO, "--state", "open", "--limit", "200", "--json", "number,labels")) if not DRY else []
    for i in issues:
        if any(l["name"] in {f"sprint-{n}" for n in sprints} for l in i["labels"]):
            gh("issue", "close", str(i["number"]), "--repo", REPO, "--comment", "Done – merged via the sprint PRs.")
    print("Closed issues of sprints", sprints, "(the Project's built-in workflow sets Status = Done on close).")


def main():
    global DRY
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--close", nargs="*", type=int)
    a = ap.parse_args()
    DRY = a.dry_run
    if a.close:
        close_sprints(a.close)
        return
    print("Labels..."); ensure_labels()
    print("Milestones..."); ensure_milestones()
    print("Issues..."); urls = create_issues()
    print("Project..."); setup_project(urls)
    print(f"{len(STORIES)} stories, {sum(s[3] for s in STORIES)} story points.")


if __name__ == "__main__":
    main()
