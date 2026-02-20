using System;
using System.Collections.Generic;
using System.Linq;
using System.Threading.Tasks;

using System.ComponentModel.DataAnnotations;
using System.Text.Json.Serialization;
using Interno.Users.Entities;

namespace Interno.Users.Models
{
    public class AuthenticateResponse
    {
        public int Id { get; set; }
        public string Firstname { get; set; }
        public string Lastname { get; set; }
        public string Username { get; set; }
        public string JwtToken { get; set; }
        [JsonIgnore]
        public string RefreshToken { get; set; }

        public AuthenticateResponse(Interno.Users.Entities.User users, string jwtToken, string refreshToken)
        {
            Id = users.Id;
            Username = users.Username;
            JwtToken = jwtToken;
            RefreshToken = refreshToken;
        }
    }
}