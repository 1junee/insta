---
name: insta-design
description: insta의 templates 화면(HTML · CSS)을 꾸밀 때 쓴다. design/DESIGN.md의 디자인과 SCREENS.md의 화면 약속을 지키며 한 페이지씩 고친다.
---

# insta 화면 꾸미기

## 순서

1. `design/DESIGN.md`를 읽고, 거기 적힌 `ref/` 레퍼런스 화면을 본다. 비어 있는 항목은 지어내지 않고, 고치기 전에 물어본다.
2. `SCREENS.md`에서 이 페이지의 주소 · 템플릿 · 받는 변수 · 폼 칸 `name` · `action`을 확인한다. 이 페이지가 `SCREENS.md`에 없으면 고치지 않고, 적어 달라고 한다.
3. 부탁받은 템플릿 하나와 `static/style.css`만 고친다.
   - 배경 · 색 · 왼쪽 메뉴 · 글꼴처럼 모든 페이지에 걸리는 것은 `base.html` 몫이다. 처음에는 `base.html`부터 꾸민다.
   - 다른 페이지를 꾸밀 때 `base.html`에서 할 일이 보이면 고치지 않고 보고에 적는다.
4. `base.html`에 Bootstrap CDN 줄이 없으면 CSS 줄은 `<head>` 안 `/static/style.css` 줄 **위**에, JS 줄은 `</body>` 바로 위에 넣는다. Bootstrap Icons CSS 줄도 `/static/style.css` 줄 **위**에 넣는다.

## 끝나면 보고

1. `DESIGN.md` 항목마다 — 어떤 클래스나 CSS로 반영했는지. 고친 HTML · CSS를 `파일:줄`과 함께 코드 조각으로 들고 와서, 그 줄이 무엇을 하는지 설명한다
   - 학생은 HTML · CSS 문법을 아직 잘 모른다. 처음 나오는 태그 · 속성 · 클래스 · CSS 속성은 하나씩 쉬운 말로 푼다
   - 코드 조각마다 세 가지를 적는다: **화면에서 보이는 것**(무엇이 어떻게 보이나) → **줄마다 뜻**(`속성: 값`을 우리말로) → **없으면 어떻게 되나**
   - 숫자(`px` · `%` · `4 / 5` 등)는 무엇의 크기인지 적는다
   - 앞 보고에서 이미 푼 문법은 "앞에서 본 `d-flex`"처럼 짧게 짚고 넘어간다
2. 참고한 공식 문서 주소
3. `SCREENS.md` 약속 확인 표

| 약속 | 고치기 전 | 고친 뒤 | 같음 |
| --- | --- | --- | --- |
| 받는 변수 | `posts` | `posts` | O |
| 폼 `action` · `method` | … | … | O |
| 입력 칸 `name` | … | … | O |
| 링크 `href` | … | … | O |

4. 브라우저에서 확인할 곳 — 어느 페이지의 어느 부분을 보면 되는지