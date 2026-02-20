using System;
using System.Collections.Generic;
using System.Linq;
using System.Threading.Tasks;

using System.Security.Claims;
using System.Security.Cryptography;
using System.IdentityModel.Tokens.Jwt;
using System.Text;
using Microsoft.Extensions.Options;
using Microsoft.IdentityModel.Tokens;

using Interno.Users.Models;
using Interno.Users.Entities;
using Interno.Users.Helpers;

namespace Interno.Users.Services
{
    public interface IUserServices
    {
        Interno.Users.Models.AuthenticateResponse Authenticate(Interno.Users.Models.AuthenticateRequest model, string ipAddress);
        Interno.Users.Models.AuthenticateResponse RefreshToken(string token, string ipAddress);
        bool RevokeToken(string token, string ipAddress);
        IEnumerable<User> GetAll();
        Interno.Users.Entities.User GetById(int id);
    }
    public class UserService : IUserServices
    {
        private Interno.Users.Helpers.UserContext _context;
        private readonly Interno.Users.Helpers.AppSettings _appSettings;

        public UserService(
            Interno.Users.Helpers.UserContext context,
            IOptions<AppSettings> appSettings)
        {
            _context = context;
            _appSettings = appSettings.Value;
        }

        public AuthenticateResponse Authenticate(AuthenticateRequest model, string ipAddress)
        {
            Interno.Users.Entities.User user = _context.User.SingleOrDefault(u => u.Username == model.Username && u.Password == model.Password);
            if(user  == null) return null;
            var jwtToken = generateJwtToken(user);
            var refreshToken = generateRefreshToken(ipAddress);

            user.RefreshTokens.Add(refreshToken);
            _context.Update(user);
            _context.SaveChanges();
            return new AuthenticateResponse(user,jwtToken,refreshToken.Token);
        }

        public AuthenticateResponse RefreshToken(string token, string ipAddress)
        {
            var user = _context.User.SingleOrDefault(u => u.RefreshTokens.Any(t => t.Token == token));

            if(user == null) return null;

            var refreshToken = user.RefreshTokens.Single(x => x.Token == token);

            if(!refreshToken.IsActive) return null;

            var newRefreshToken = generateRefreshToken(ipAddress);
            refreshToken.Revoked = DateTime.UtcNow;
            refreshToken.RevokedByIp  = ipAddress;
            refreshToken.RevokedByToken = newRefreshToken.Token;

            user.RefreshTokens.Add(newRefreshToken);
            _context.Update(user);
            _context.SaveChanges();

            var jwtToken = generateJwtToken(user);
            return new AuthenticateResponse(user,jwtToken,newRefreshToken.Token);
        }
        public bool RevokeToken(string token, string ipAddress)
        {
            var user = _context.User.SingleOrDefault(u => u.RefreshTokens.Any(t => t.Token == token));
            if(user == null) return false;
            var refreshToken = user.RefreshTokens.Single(x => x.Token == token);
            if(!refreshToken.IsActive) return false;
            refreshToken.Revoked = DateTime.UtcNow;
            refreshToken.RevokedByIp = ipAddress;
            _context.Update(user);
            _context.SaveChanges();
            return true;
        }


        public IEnumerable<Interno.Users.Entities.User> GetAll() => _context.User;
        public Interno.Users.Entities.User GetById(int id) => _context.User.Find(id);
        private string generateJwtToken(Interno.Users.Entities.User user)
        {
            var tokenHandler = new JwtSecurityTokenHandler();
            var key = Encoding.ASCII.GetBytes(_appSettings.Secret);
            var tokenDescriptor = new SecurityTokenDescriptor
            {
                Subject = new ClaimsIdentity(new Claim[]{
                    new Claim(ClaimTypes.Name, user.Id.ToString())
                }),
                Expires = DateTime.UtcNow.AddMinutes(15),
                SigningCredentials   = new SigningCredentials(new SymmetricSecurityKey(key), SecurityAlgorithms.HmacSha256Signature)
            };
            var token = tokenHandler.CreateToken(tokenDescriptor);
            return tokenHandler.WriteToken(token);
        }
        private RefreshToken generateRefreshToken(string ipAddress)
        {
            using(var rngCryptoServiceProvider = new RNGCryptoServiceProvider())
            {
                var randomBytes = new Byte[64];
                rngCryptoServiceProvider.GetBytes(randomBytes);
                return new RefreshToken
                {
                    Token = Convert.ToBase64String(randomBytes),
                    Expires = DateTime.UtcNow.AddDays(7),
                    Created = DateTime.UtcNow,
                    CreatedByIp = ipAddress
                };
            }
        }

    }
}