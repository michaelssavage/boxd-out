const handler = async function (event, context) {
  await fetch("/.netlify/functions/scraper", {
    method: "POST",
  });

  return {
    statusCode: 200,
  };
};

module.exports.handler = handler;

module.exports.config = {
  schedule: "@daily",
};
