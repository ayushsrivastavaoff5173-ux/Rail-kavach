# Contributing to Rail Kavach

Contribute karne ke liye shukriya! Neeche simple workflow diya hai.

## Workflow

1. Repo ko fork karein (ya team member hain to direct clone karein).
2. Naya branch banayein: `git checkout -b feature/short-description`
3. Changes karein aur chhote, clear commits banayein.
4. Push karein: `git push origin feature/short-description`
5. `main` branch ke against Pull Request kholein.

## Branch Naming

- `feature/...` naye features ke liye
- `fix/...` bug fixes ke liye
- `docs/...` documentation ke liye

## Commit Messages

Short aur descriptive rakhein, e.g. `Add train signal parser`, `Fix sensor timeout bug`.

## Pull Request Checklist

- [ ] Code chal raha hai aur tests pass ho rahe hain
- [ ] README/docs update kiye (agar zaroorat ho)
- [ ] PR description mein change ka reason likha hai

## Rules

- `main` branch par direct push na karein.
- Secrets (API keys, passwords) kabhi commit na karein.
