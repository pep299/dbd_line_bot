module.exports = {
  test: (val: unknown) => typeof val === "string",
  print: (val: unknown) => {
    const newVal = (val as string).replace(
      /([A-Fa-f0-9]{64})(\.zip)/,
      "[HASH REMOVED]"
    ).replace(
      /^[A-Za-z0-9\+=/]{172}$|^[A-Za-z0-9]{50}$|^[A-Za-z0-9\-]{50}$|^[A-Za-z0-9]{45}$|^[a-f0-9]{32}$|^[A-Za-z0-9]{25}$/,
      "[SEC REMOVED]"
    );
    return `"${newVal}"`;
  },
};
