# Tempo Budget — directives projet

Instructions persistantes. À suivre sans qu'on te le redise.

## Langue

- Conversation utilisateur : **français**.
- Code, commits, commentaires, strings techniques : **anglais** (cohérent avec l'historique).
- UI : `t('...')` avec `fr.json` + `en.json` **toujours synchronisés**.

## Stack (rappel rapide)

- Frontend : Vue 3 + TS + Naive UI + Pinia + vue-i18n + Chart.js — API dans `frontend/src/services/api.ts`, stores Pinia par domaine, locales `frontend/src/locales/{fr,en}.json`.
- Backend : FastAPI + SQLite (aiosqlite) + raw SQL via `text()` + Pydantic. Migrations dans `backend/migrations/*.sql`, appliquées au démarrage.
- Auth : JWT, `get_current_user` injecte `user_id`.

## Commits

- Convention : `feat: …`, `fix: …`, `chore: …`, `refactor: …`, `docs: …` — sujet court à l'impératif, en anglais.
- **Jamais** de `Co-Authored-By: Claude`, `Generated with Claude Code`, ou trailer équivalent. Commits signés uniquement par l'utilisateur.
- Stager explicitement (`git add <paths>`). Pas de `git add .` / `-A`. Pas de `--amend` (créer un nouveau commit). Pas de `--no-verify`.

## i18n (règle dure)

Toute nouvelle clé i18n est ajoutée **simultanément** dans `frontend/src/locales/fr.json` **et** `frontend/src/locales/en.json`. Structure par sections (`project.*`, `transaction.*`, etc.) cohérente entre les deux.

## Backend ↔ Frontend

Quand tu touches une route ou un modèle Pydantic : vérifie que le type TS + la méthode `*API` + le store Pinia consommateur sont synchros. Une nouvelle table ou colonne = un fichier dans `backend/migrations/` (appliqué au démarrage).

## Feature user-visible → README

Toute feature visible par l'utilisateur final doit être ajoutée dans la section pertinente de `README.md` avant de tagger. Fixes internes, refactors, migrations silencieuses : pas concerné.

## Tag + release (workflow complet)

Quand l'utilisateur dit « tag et push » ou équivalent après un changement mergé :

1. **Bump** depuis le dernier tag (`git describe --tags --abbrev=0`) :
   - commits `feat:` présents → **minor** (`v2.3.0` → `v2.4.0`)
   - uniquement `fix:`/`chore:`/`refactor:`/`docs:` → **patch** (`v2.3.0` → `v2.3.1`)
   - breaking change explicite → **major**
2. **Synchro version** dans le même commit :
   - badge `version-X.Y.Z-blue` dans `README.md`
   - `"version"` dans `frontend/package.json`
   - section « Recent Changes » en bas du `README.md` (remplacer par la nouvelle version + bullets)
3. `chore: bump to vX.Y.Z` puis `git tag vX.Y.Z && git push origin <branch> && git push origin vX.Y.Z`.
4. **GitHub Release** via `gh release create vX.Y.Z` :
   - Titre : `vX.Y.Z - <Thème court>` pour minor/major, juste `vX.Y.Z` pour un patch.
   - Body :
     ```
     ## What's New

     - <bullet par feature/fix user-visible, résumé, pas un dump de git log>

     ## Full Changelog
     https://github.com/jdenozi/TempoBudget/compare/<prev_tag>...<new_tag>
     ```

Écart actuel : tags git jusqu'à `v2.3.0`, GitHub Releases jusqu'à `v0.15.0`. Ne pas rétro-combler sans demande explicite.

## Ne pas faire

- Créer de nouveaux fichiers `.md` (doc, notes, plans) sauf si demandé.
- Mettre à jour uniquement `fr.json` ou uniquement `en.json`.
- Tagger sans mettre à jour badge README + `package.json` dans le même workflow.
- Ajouter des commentaires qui paraphrasent le code ; ne commenter que le *pourquoi* non évident.
