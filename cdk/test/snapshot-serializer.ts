module.exports = {
  test: (val: unknown) => typeof val === "string",
  print: (val: unknown) => {
    const newVal = (val as string).replace(
      /([A-Fa-f0-9]{64})(\.zip)/,
      "[HASH REMOVED]"
    ).replace(
      /^[A-Za-z0-9\+=/]{172}$|^[A-Za-z0-9%]{112}$|^[a-f0-9]{32}$/,
      "[SEC REMOVED]"
    );
    return `"${newVal}"`;
  },
};
