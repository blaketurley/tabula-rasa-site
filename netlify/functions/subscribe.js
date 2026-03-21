// subscribe.js — Netlify Function
// Handles newsletter signups for Tabula Rasa podcast
// Adds to Encharge with tags, sends confirmation via Emailit

const ENCHARGE_API = "https://api.encharge.io/v1";
const ENCHARGE_TOKEN = process.env.ENCHARGE_TOKEN;
const EMAILIT_API = "https://api.emailit.com/v2/emails";
const EMAILIT_KEY = process.env.EMAILIT_KEY;

exports.handler = async (event) => {
  // CORS headers
  const headers = {
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Headers": "Content-Type",
    "Access-Control-Allow-Methods": "POST, OPTIONS",
    "Content-Type": "application/json",
  };

  if (event.httpMethod === "OPTIONS") {
    return { statusCode: 200, headers, body: "" };
  }

  if (event.httpMethod !== "POST") {
    return { statusCode: 405, headers, body: JSON.stringify({ error: "Method not allowed" }) };
  }

  let email;
  try {
    const body = JSON.parse(event.body);
    email = body.email;
  } catch {
    // Try form-encoded
    const params = new URLSearchParams(event.body);
    email = params.get("email");
  }

  if (!email || !email.includes("@")) {
    return { statusCode: 400, headers, body: JSON.stringify({ error: "Valid email required" }) };
  }

  const errors = [];

  // 1. Add to Encharge with tags
  try {
    const res = await fetch(`${ENCHARGE_API}/people`, {
      method: "POST",
      headers: {
        "X-Encharge-Token": ENCHARGE_TOKEN,
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        type: "people",
        people: [{
          email: email,
          tags: "Tabula Rasa,source:podcast-newsletter,intent:information",
          signup_source: "tabula-rasa-newsletter",
        }],
      }),
    });

    if (!res.ok) {
      const err = await res.text();
      errors.push(`Encharge: ${res.status} ${err}`);
    }
  } catch (e) {
    errors.push(`Encharge: ${e.message}`);
  }

  // 2. Send welcome email via Emailit
  try {
    const res = await fetch(EMAILIT_API, {
      method: "POST",
      headers: {
        Authorization: `Bearer ${EMAILIT_KEY}`,
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        from: "Blake Turley <hello@mail.turleylaw.com>",
        to: email,
        reply_to: "hello@turleylaw.com",
        subject: "Welcome to Tabula Rasa",
        html: `
          <div style="font-family: Georgia, serif; max-width: 560px; margin: 0 auto; padding: 40px 20px; color: #333;">
            <h1 style="font-size: 28px; font-weight: normal; font-style: italic; margin-bottom: 24px;">Welcome to Tabula Rasa.</h1>
            <p style="font-size: 17px; line-height: 1.7;">You're in. New episodes, behind-the-scenes notes, and the occasional 2 AM thought I couldn't keep to myself.</p>
            <p style="font-size: 17px; line-height: 1.7;">In the meantime, check out the latest episodes at <a href="https://tabularasawithblaketurley.com" style="color: #0080FF;">tabularasawithblaketurley.com</a>.</p>
            <p style="font-size: 17px; line-height: 1.7; margin-top: 32px;">&mdash; Blake</p>
            <hr style="border: none; border-top: 1px solid #eee; margin: 32px 0;">
            <p style="font-size: 12px; color: #999;">Tabula Rasa is a podcast by Blake Turley. <a href="https://turleylaw.com/unsubscribe" style="color: #999;">Unsubscribe</a></p>
          </div>
        `,
      }),
    });

    if (!res.ok) {
      const err = await res.text();
      errors.push(`Emailit: ${res.status} ${err}`);
    }
  } catch (e) {
    errors.push(`Emailit: ${e.message}`);
  }

  // 3. Notify Blake
  try {
    await fetch(EMAILIT_API, {
      method: "POST",
      headers: {
        Authorization: `Bearer ${EMAILIT_KEY}`,
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        from: "Tabula Rasa Bot <hello@mail.turleylaw.com>",
        to: "blake@turleylaw.com",
        subject: `New Tabula Rasa subscriber: ${email}`,
        text: `New subscriber from tabularasawithblaketurley.com:\n\n${email}\n\nAdded to Encharge with tags: Tabula Rasa, source:podcast-newsletter, intent:information`,
      }),
    });
  } catch (e) {
    // Non-critical, don't fail
  }

  if (errors.length > 0) {
    console.error("Subscribe errors:", errors);
    // Still return success to user — they signed up, backend issues aren't their problem
  }

  return {
    statusCode: 200,
    headers,
    body: JSON.stringify({ success: true, message: "You're in! Check your email." }),
  };
};
