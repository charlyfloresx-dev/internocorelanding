using System;
using System.Collections.Generic;
using System.Linq;
using System.Threading.Tasks;

using System.ComponentModel.DataAnnotations;
using System.Text.Json.Serialization;
using Microsoft.EntityFrameworkCore;

namespace Interno.Users.Entities
{
    [Owned]
    public class RefreshToken
    {
        [Key]
        [JsonIgnore]
        public int Id { get; set; }
        public string Token { get; set; }
        public DateTime Expires { get; set; }
        public bool IsExpired => DateTime.UtcNow >= Expires;
        public DateTime Created { get; set; }
        public string CreatedByIp { get; set; }
        public DateTime? Revoked { get; set; }
        public string RevokedByIp { get; set; }
        public string RevokedByToken { get; set; }
        public bool IsActive => Revoked == null && !IsExpired;
        
    }
}