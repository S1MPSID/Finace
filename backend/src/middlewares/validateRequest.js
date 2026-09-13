export function validateRequest(validator) {
  return function runValidation(req, _res, next) {
    try {
      req.validated = validator(req);
      next();
    } catch (error) {
      next(error);
    }
  };
}
